from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CandidateJobScore, Job, JobAIAnalysis
from ..scoring_schemas import AIJobScoreResult
from .candidate_profile import CandidateProfileData, CandidateProfileService


PROMPT_VERSION = "job-fit-v1"


class JobScoringProvider(Protocol):
    model: str

    async def score(
        self,
        profile: CandidateProfileData,
        job_payload: dict[str, object],
    ) -> AIJobScoreResult:
        ...


class ScoringProviderError(RuntimeError):
    pass


def weighted_fit_score(result: AIJobScoreResult) -> int:
    values = result.breakdown
    total = (
        values.title_alignment
        + values.skills_match
        + values.experience_match
        + values.location_workplace
        + values.compensation
        + values.industry_company
        + values.exclusions
    )
    return max(0, min(100, total))


def job_payload(job: Job) -> dict[str, object]:
    return {
        "title": job.title,
        "location": job.location_raw,
        "city": job.city,
        "region": job.region,
        "country": job.country,
        "country_code": job.country_code,
        "workplace_type": job.workplace_type.value,
        "employment_type": job.employment_type,
        "experience_level": job.experience_level,
        "job_function": job.job_function,
        "industry": job.industry,
        "salary": {
            "raw": job.salary_raw,
            "min": str(job.salary_min) if job.salary_min is not None else None,
            "max": str(job.salary_max) if job.salary_max is not None else None,
            "currency": job.salary_currency,
            "period": job.salary_period,
        },
        "description": (job.description or "")[:14000],
        "responsibilities": job.responsibilities,
        "requirements": job.requirements,
        "preferred_qualifications": job.preferred_qualifications,
        "benefits": job.benefits,
        "skills": job.skills,
        "technologies": job.technologies,
        "certifications": job.certifications,
        "education": job.education,
        "languages": job.languages,
        "applicant_count": job.applicant_count,
    }


class JobScoringService:
    def __init__(
        self,
        session: Session,
        provider: JobScoringProvider,
        profile_service: CandidateProfileService | None = None,
    ) -> None:
        self.session = session
        self.provider = provider
        self.profile_service = profile_service or CandidateProfileService(session)

    async def score_job(
        self,
        user_id: UUID,
        job_id: UUID,
        *,
        force: bool = False,
    ) -> dict[str, object]:
        profile_result = self.profile_service.get(user_id)
        if not profile_result.exists or profile_result.profile_id is None:
            raise ValueError("candidate profile is not configured")

        job = self.session.execute(
            select(Job).where(Job.id == job_id)
        ).scalars().first()
        if job is None:
            raise ValueError("job not found")

        existing = self.session.execute(
            select(CandidateJobScore).where(
                CandidateJobScore.profile_id == profile_result.profile_id,
                CandidateJobScore.job_id == job.id,
            )
        ).scalars().first()

        if existing is not None and not force:
            return self._view(existing, profile_result.profile_id)

        result = await self.provider.score(
            profile_result.data,
            job_payload(job),
        )
        fit_score = weighted_fit_score(result)
        stored = result.model_dump(mode="json")
        stored["fit_score"] = fit_score
        now = datetime.now(timezone.utc)

        if existing is None:
            existing = CandidateJobScore(
                id=uuid4(),
                profile_id=profile_result.profile_id,
                job_id=job.id,
                fit_score=fit_score,
                confidence=result.confidence,
                breakdown=stored,
            )
            self.session.add(existing)
        else:
            existing.fit_score = fit_score
            existing.confidence = result.confidence
            existing.breakdown = stored

        self.session.add(
            JobAIAnalysis(
                id=uuid4(),
                job_id=job.id,
                profile_id=profile_result.profile_id,
                model=self.provider.model,
                prompt_version=PROMPT_VERSION,
                result=stored,
                created_at=now,
            )
        )
        self.session.flush()

        return {
            "job_id": str(job.id),
            "profile_id": str(profile_result.profile_id),
            "fit_score": fit_score,
            "confidence": result.confidence,
            "breakdown": stored,
            "model": self.provider.model,
            "prompt_version": PROMPT_VERSION,
            "created_at": now.isoformat(),
        }

    def get_existing(self, user_id: UUID, job_id: UUID) -> dict[str, object] | None:
        profile_result = self.profile_service.get(user_id)
        if profile_result.profile_id is None:
            return None
        score = self.session.execute(
            select(CandidateJobScore).where(
                CandidateJobScore.profile_id == profile_result.profile_id,
                CandidateJobScore.job_id == job_id,
            )
        ).scalars().first()
        if score is None:
            return None
        return self._view(score, profile_result.profile_id)

    def _view(self, score: CandidateJobScore, profile_id: UUID) -> dict[str, object]:
        analysis = self.session.execute(
            select(JobAIAnalysis).where(
                JobAIAnalysis.job_id == score.job_id,
                JobAIAnalysis.profile_id == profile_id,
            )
            .order_by(JobAIAnalysis.created_at.desc())
            .limit(1)
        ).scalars().first()
        return {
            "job_id": str(score.job_id),
            "profile_id": str(profile_id),
            "fit_score": score.fit_score,
            "confidence": score.confidence,
            "breakdown": score.breakdown,
            "model": analysis.model if analysis else self.provider.model,
            "prompt_version": analysis.prompt_version if analysis else PROMPT_VERSION,
            "created_at": score.created_at.isoformat(),
        }
