from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from ..models import Company, Job, JobState, Search, SearchRun


@dataclass(slots=True)
class DashboardOverview:
    total_jobs: int
    active_jobs: int
    remote_jobs: int
    new_jobs_24h: int
    companies: int
    searches: int


@dataclass(slots=True)
class DashboardJob:
    id: str
    source: str
    source_job_id: str
    title: str
    company_name: str | None
    location: str | None
    country_code: str | None
    workplace_type: str
    employment_type: str | None
    experience_level: str | None
    salary_min: str | None
    salary_max: str | None
    salary_currency: str | None
    job_state: str
    applicant_count: int | None
    apply_url: str | None
    external_apply_url: str | None
    ats_provider: str | None
    posted_at: datetime | None
    discovered_at: datetime


@dataclass(slots=True)
class DashboardSearchRun:
    id: str
    search_name: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class DashboardService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def overview(self) -> DashboardOverview:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        return DashboardOverview(
            total_jobs=self._count(Job),
            active_jobs=self._count(Job, Job.job_state == JobState.ACTIVE),
            remote_jobs=self._count(Job, Job.workplace_type == "REMOTE"),
            new_jobs_24h=self._count(Job, Job.discovered_at >= since),
            companies=self._count(Company),
            searches=self._count(Search),
        )

    def list_jobs(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        query: str | None = None,
        state: str | None = None,
        remote_only: bool = False,
        country_code: str | None = None,
    ) -> tuple[int, list[DashboardJob]]:
        base: Select[tuple[Job]] = select(Job)
        if query:
            pattern = f"%{query.strip()}%"
            base = base.outerjoin(Job.company).where(
                or_(
                    Job.title.ilike(pattern),
                    Job.normalized_title.ilike(pattern),
                    Company.name.ilike(pattern),
                )
            )
        if state:
            try:
                base = base.where(Job.job_state == JobState(state.upper()))
            except ValueError:
                base = base.where(Job.job_state == JobState.ERROR)
        if remote_only:
            base = base.where(Job.workplace_type == "REMOTE")
        if country_code:
            base = base.where(Job.country_code == country_code.upper())

        count_stmt = select(func.count()).select_from(base.order_by(None).subquery())
        total = int(self.session.scalar(count_stmt) or 0)
        stmt = (
            base.options(joinedload(Job.company))
            .order_by(Job.discovered_at.desc(), Job.id.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = self.session.execute(stmt).scalars().unique().all()
        return total, [self._job(row) for row in rows]

    def recent_search_runs(self, *, limit: int = 10) -> list[DashboardSearchRun]:
        stmt = (
            select(SearchRun, Search.name)
            .outerjoin(Search, Search.id == SearchRun.search_id)
            .order_by(SearchRun.created_at.desc())
            .limit(limit)
        )
        rows = self.session.execute(stmt).all()
        return [
            DashboardSearchRun(
                id=str(run.id),
                search_name=name or "Unnamed search",
                status=run.status,
                started_at=run.started_at,
                finished_at=run.finished_at,
                created_at=run.created_at,
            )
            for run, name in rows
        ]

    def _count(self, model: type, *conditions: object) -> int:
        stmt = select(func.count()).select_from(model)
        if conditions:
            stmt = stmt.where(*conditions)
        return int(self.session.scalar(stmt) or 0)

    @staticmethod
    def _job(job: Job) -> DashboardJob:
        return DashboardJob(
            id=str(job.id),
            source=job.source,
            source_job_id=job.source_job_id,
            title=job.title,
            company_name=job.company.name if job.company else None,
            location=job.location_raw,
            country_code=job.country_code,
            workplace_type=job.workplace_type.value,
            employment_type=job.employment_type,
            experience_level=job.experience_level,
            salary_min=str(job.salary_min) if job.salary_min is not None else None,
            salary_max=str(job.salary_max) if job.salary_max is not None else None,
            salary_currency=job.salary_currency,
            job_state=job.job_state.value,
            applicant_count=job.applicant_count,
            apply_url=job.apply_url,
            external_apply_url=job.external_apply_url,
            ats_provider=job.ats_provider,
            posted_at=job.posted_at,
            discovered_at=job.discovered_at,
        )
