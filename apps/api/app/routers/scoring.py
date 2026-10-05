from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..providers.openai_scoring import OpenAIResponsesScoringProvider
from ..scoring_schemas import JobScoreRequest, JobScoreResponse
from ..services.job_scoring_core import JobScoringService, ScoringProviderError
from ..settings import settings


router = APIRouter(prefix="/api/v1/jobs", tags=["scoring"])
db_dependency = Depends(get_db)


def provider() -> OpenAIResponsesScoringProvider:
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="OpenAI scoring is not configured")
    return OpenAIResponsesScoringProvider(
        settings.openai_api_key,
        model=settings.openai_model,
    )


def response(data: dict[str, object]) -> JobScoreResponse:
    breakdown = data["breakdown"]
    return JobScoreResponse(
        job_id=str(data["job_id"]),
        profile_id=str(data["profile_id"]),
        fit_score=int(data["fit_score"]),
        confidence=data["confidence"],
        breakdown=breakdown,
        matched_skills=list(breakdown.get("matched_skills", [])),
        missing_skills=list(breakdown.get("missing_skills", [])),
        strengths=list(breakdown.get("strengths", [])),
        concerns=list(breakdown.get("concerns", [])),
        recommendation=str(breakdown.get("recommendation", "")),
        summary=str(breakdown.get("summary", "")),
        model=str(data["model"]),
        prompt_version=str(data["prompt_version"]),
        created_at=str(data["created_at"]),
    )


@router.post("/{job_id}/score", response_model=JobScoreResponse)
async def score_job(
    job_id: UUID,
    payload: JobScoreRequest,
    session: Session = db_dependency,
) -> JobScoreResponse:
    try:
        data = await JobScoringService(session, provider()).score_job(
            UUID(settings.default_user_id),
            job_id,
            force=payload.force,
        )
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ScoringProviderError as exc:
        session.rollback()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="job scoring failed") from exc
    return response(data)


@router.get("/{job_id}/score", response_model=JobScoreResponse)
def get_job_score(
    job_id: UUID,
    session: Session = db_dependency,
) -> JobScoreResponse:
    data = JobScoringService(session, provider()).get_existing(
        UUID(settings.default_user_id),
        job_id,
    )
    if data is None:
        raise HTTPException(status_code=404, detail="job score not found")
    return response(data)
