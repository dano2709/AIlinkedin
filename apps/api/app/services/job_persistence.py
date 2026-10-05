from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.detail import CanonicalCompany, CanonicalRecord
from ..models import Company, Job, JobSnapshot, JobSource, JobState, WorkplaceType
from .job_history import snapshot_hashes, snapshot_payload


@dataclass(slots=True)
class PersistenceResult:
    job: Job
    created: bool
    deduplicated: bool
    snapshot_created: bool
    company_created: bool


class JobPersistenceService:
    """Persist canonical jobs while preserving identity and change history."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(
        self,
        canonical: CanonicalRecord,
        *,
        search_run_id: UUID | None = None,
        discovered_from: str | None = None,
    ) -> PersistenceResult:
        company, company_created = self._upsert_company(canonical.company)
        existing = self._find_existing_job(canonical, company)
        deduplicated = existing is not None and existing.source_job_id != canonical.source_id
        created = existing is None

        job = existing or Job(
            id=uuid4(),
            source=canonical.source,
            source_job_id=canonical.source_id,
            discovered_at=canonical.scraped_at,
        )
        previous_hashes = self._last_snapshot_hashes(job) if not created else None

        self._apply_job(job, canonical, company, search_run_id, preserve_source_identity=deduplicated)
        self._upsert_source(job, canonical, search_run_id, discovered_from)
        snapshot_created = self._create_snapshot_if_changed(
            job,
            canonical,
            previous_hashes,
            force=created,
        )

        if created:
            self.session.add(job)
        self.session.flush()

        return PersistenceResult(
            job=job,
            created=created,
            deduplicated=deduplicated,
            snapshot_created=snapshot_created,
            company_created=company_created,
        )

    def _upsert_company(
        self,
        canonical: CanonicalCompany | None,
    ) -> tuple[Company | None, bool]:
        if canonical is None:
            return None, False

        normalized_name = (canonical.name or "").casefold().strip()
        company = None

        if canonical.source_company_id:
            company = self.session.execute(
                select(Company).where(
                    Company.source == "linkedin",
                    Company.source_company_id == canonical.source_company_id,
                )
            ).scalars().first()

        if company is None and normalized_name:
            company = self.session.execute(
                select(Company).where(
                    Company.source == "linkedin",
                    Company.normalized_name == normalized_name,
                )
            ).scalars().first()

        created = company is None
        if created:
            company = Company(
                id=uuid4(),
                source="linkedin",
                source_company_id=canonical.source_company_id,
                name=canonical.name or "Unknown",
                normalized_name=normalized_name or "unknown",
                url=canonical.url,
                enrichment={},
            )

        company.name = canonical.name or company.name
        company.normalized_name = normalized_name or company.normalized_name
        company.url = canonical.url or company.url
        company.enrichment = {
            **(company.enrichment or {}),
            "website": canonical.website,
            "logo_url": canonical.logo_url,
            "employee_count": canonical.employee_count,
            "industry": canonical.industry,
            "industries": canonical.industries,
            "description": canonical.description,
            "tagline": canonical.tagline,
            "headquarters": canonical.headquarters,
            "employee_size": canonical.employee_size,
            "follower_count": canonical.follower_count,
            "company_type": canonical.company_type,
            "founded_year": canonical.founded_year,
            **canonical.enrichment,
        }
        company.enrichment = {
            key: value for key, value in company.enrichment.items() if value is not None
        }

        if created:
            self.session.add(company)
            self.session.flush()

        return company, created

    def _find_existing_job(
        self,
        canonical: CanonicalRecord,
        company: Company | None,
    ) -> Job | None:
        job = self.session.execute(
            select(Job).where(
                Job.source == canonical.source,
                Job.source_job_id == canonical.source_id,
            )
        ).scalars().first()
        if job is not None:
            return job

        job = self.session.execute(
            select(Job).where(Job.canonical_url == canonical.url)
        ).scalars().first()
        if job is not None:
            return job

        if canonical.external_apply_url:
            job = self.session.execute(
                select(Job).where(Job.external_apply_url == canonical.external_apply_url)
            ).scalars().first()
            if job is not None:
                return job

        candidates = self.session.execute(
            select(Job).where(
                Job.normalized_title == canonical.normalized_title,
                Job.country_code == canonical.country_code,
            ).limit(25)
        ).scalars().all()

        company_id = company.id if company else None
        company_name = company.normalized_name if company else None

        for candidate in candidates:
            score = 0
            if company_id and candidate.company_id == company_id:
                score += 4
            elif company_name and candidate.company is not None:
                if candidate.company.normalized_name == company_name:
                    score += 4
            if candidate.city and canonical.city and candidate.city == canonical.city:
                score += 2
            if (
                candidate.location_raw
                and canonical.location_raw
                and candidate.location_raw == canonical.location_raw
            ):
                score += 2
            if (
                candidate.job_function
                and canonical.job_function
                and candidate.job_function == canonical.job_function
            ):
                score += 1
            if (
                candidate.employment_type
                and canonical.employment_type
                and candidate.employment_type == canonical.employment_type
            ):
                score += 1
            if score >= 6:
                return candidate

        return None

    @staticmethod
    def _apply_job(
        job: Job,
        canonical: CanonicalRecord,
        company: Company | None,
        search_run_id: UUID | None,
        *,
        preserve_source_identity: bool = False,
    ) -> None:
        job.company_id = company.id if company else None
        job.source = canonical.source
        if not preserve_source_identity:
            job.source_job_id = canonical.source_id
        job.canonical_url = canonical.url
        job.title = canonical.title
        job.normalized_title = canonical.normalized_title
        job.location_raw = canonical.location_raw
        job.city = canonical.city
        job.region = canonical.region
        job.country = canonical.country
        job.country_code = canonical.country_code
        job.workplace_type = WorkplaceType(canonical.workplace_type)
        job.remote_allowed = canonical.remote_allowed
        job.posted_at = canonical.posted_at
        job.posted_at_raw = canonical.posted_at_raw
        job.posted_at_precision = canonical.posted_at_precision
        job.employment_type = canonical.employment_type
        job.experience_level = canonical.experience_level
        job.job_function = canonical.job_function
        job.industry = canonical.industry
        job.salary_raw = canonical.salary_raw
        job.salary_min = canonical.salary_min
        job.salary_max = canonical.salary_max
        job.salary_currency = canonical.salary_currency
        job.salary_period = canonical.salary_period
        job.description = canonical.description
        job.responsibilities = canonical.responsibilities
        job.requirements = canonical.requirements
        job.preferred_qualifications = canonical.preferred_qualifications
        job.benefits = canonical.benefits
        job.skills = canonical.skills
        job.technologies = canonical.technologies
        job.certifications = canonical.certifications
        job.education = canonical.education
        job.languages = canonical.languages
        job.applicant_count = canonical.applicant_count
        job.apply_type = canonical.apply_type
        job.apply_url = canonical.apply_url
        job.external_apply_url = canonical.external_apply_url
        job.ats_provider = canonical.ats_provider
        job.job_state = JobState(canonical.state)
        job.reposted = canonical.reposted
        job.scraped_at = canonical.scraped_at
        job.extractor_version = canonical.extractor_version
        if search_run_id is not None:
            job.search_run_id = search_run_id

    def _upsert_source(
        self,
        job: Job,
        canonical: CanonicalRecord,
        search_run_id: UUID | None,
        discovered_from: str | None,
    ) -> None:
        source = self.session.execute(
            select(JobSource).where(
                JobSource.job_id == job.id,
                JobSource.source == canonical.source,
                JobSource.source_url == canonical.url,
            )
        ).scalars().first()

        if source is None:
            self.session.add(
                JobSource(
                    id=uuid4(),
                    job_id=job.id,
                    source=canonical.source,
                    source_url=canonical.url,
                    discovered_from=discovered_from,
                    search_run_id=search_run_id,
                    provenance=canonical.provenance,
                )
            )
            return

        source.discovered_from = discovered_from or source.discovered_from
        source.search_run_id = search_run_id or source.search_run_id
        source.provenance = {**(source.provenance or {}), **canonical.provenance}

    def _last_snapshot_hashes(self, job: Job) -> dict[str, str] | None:
        latest = self.session.execute(
            select(JobSnapshot)
            .where(JobSnapshot.job_id == job.id)
            .order_by(JobSnapshot.captured_at.desc())
            .limit(1)
        ).scalars().first()

        if latest is None:
            return None

        return {
            "description_hash": latest.description_hash or "",
            "requirements_hash": latest.requirements_hash or "",
            "salary_hash": latest.salary_hash or "",
            "location_hash": latest.location_hash or "",
            "apply_url_hash": latest.apply_url_hash or "",
            "applicant_count": str(latest.applicant_count),
            "title": latest.title,
        }

    def _create_snapshot_if_changed(
        self,
        job: Job,
        canonical: CanonicalRecord,
        previous_hashes: dict[str, str] | None,
        *,
        force: bool,
    ) -> bool:
        hashes = snapshot_hashes(canonical)
        current = {
            **hashes,
            "applicant_count": str(canonical.applicant_count),
            "title": canonical.title,
        }
        if not force and previous_hashes == current:
            return False

        self.session.add(
            JobSnapshot(
                id=uuid4(),
                job_id=job.id,
                captured_at=canonical.scraped_at,
                title=canonical.title,
                description_hash=hashes["description_hash"],
                requirements_hash=hashes["requirements_hash"],
                salary_hash=hashes["salary_hash"],
                location_hash=hashes["location_hash"],
                apply_url_hash=hashes["apply_url_hash"],
                applicant_count=canonical.applicant_count,
                payload=snapshot_payload(canonical),
            )
        )
        return True


def _canonical_from_job(job: Job) -> CanonicalRecord:
    return CanonicalRecord(
        source=job.source,
        source_id=job.source_job_id,
        url=job.canonical_url,
        title=job.title,
        normalized_title=job.normalized_title,
        location_raw=job.location_raw,
        city=job.city,
        region=job.region,
        country=job.country,
        country_code=job.country_code,
        workplace_type=job.workplace_type.value,
        remote_allowed=job.remote_allowed,
        posted_at=job.posted_at,
        posted_at_raw=job.posted_at_raw,
        posted_at_precision=job.posted_at_precision,
        employment_type=job.employment_type,
        experience_level=job.experience_level,
        job_function=job.job_function,
        industry=job.industry,
        salary_raw=job.salary_raw,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        salary_period=job.salary_period,
        description=job.description,
        responsibilities=job.responsibilities,
        requirements=job.requirements,
        preferred_qualifications=job.preferred_qualifications,
        benefits=job.benefits,
        skills=job.skills,
        technologies=job.technologies,
        certifications=job.certifications,
        education=job.education,
        languages=job.languages,
        applicant_count=job.applicant_count,
        apply_type=job.apply_type,
        apply_url=job.apply_url,
        external_apply_url=job.external_apply_url,
        ats_provider=job.ats_provider,
        state=job.job_state.value,
        reposted=job.reposted,
        scraped_at=job.scraped_at,
        extractor_version=job.extractor_version or "unknown",
        company=None,
        provenance={},
        signals={},
    )
