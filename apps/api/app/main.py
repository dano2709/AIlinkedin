from dataclasses import asdict
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .candidate_profile_schemas import (
    CandidateProfileInput,
    CandidateProfileResponse,
    CandidateProfileUpdateResponse,
)
from .dashboard_schemas import (
    DashboardJobResponse,
    DashboardJobsResponse,
    DashboardOverviewResponse,
    DashboardSearchRunResponse,
    DashboardSearchRunsResponse,
)
from .db import get_db
from .domain import (
    JobDetailExtractor,
    JobDetailInput,
    JobSearchInput,
    SearchQuery,
    SearchQueryCompiler,
)
from .providers.apify_linkedin import ApifyLinkedInAdapter, ProviderError
from .schemas import (
    CompiledSearchResponse,
    JobCandidateResponse,
    JobDetailRequest,
    JobDetailResponse,
    JobImportRequest,
    JobImportResponse,
    ProviderSearchResponse,
    SearchQueryInput,
)
from .services.candidate_profile import (
    CandidateProfileData,
    CandidateProfileResult,
    CandidateProfileService,
)
from .services.dashboard import DashboardService
from .services.job_import import ApifyJobImportService
from .settings import settings

app = FastAPI(
    title=settings.app_name,
    version="0.7.0",
    description="LinkedIn Job Intelligence API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)

compiler = SearchQueryCompiler()
detail_extractor = JobDetailExtractor()
db_dependency = Depends(get_db)


def _apify_adapter() -> ApifyLinkedInAdapter:
    if not settings.apify_api_token:
        raise HTTPException(status_code=503, detail="Apify provider is not configured")
    return ApifyLinkedInAdapter(
        token=settings.apify_api_token,
        actor_id=settings.apify_actor_id,
        base_url=settings.apify_base_url,
        timeout_seconds=settings.apify_timeout_seconds,
    )


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/api/v1/meta", tags=["system"])
def meta() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": "0.7.0",
        "status": "phase-7",
    }


@app.post("/api/v1/searches/compile", response_model=CompiledSearchResponse, tags=["search"])
def compile_search(payload: SearchQueryInput) -> CompiledSearchResponse:
    compiled = compiler.compile(SearchQuery(**payload.model_dump()))
    return CompiledSearchResponse(
        search_text=compiled.search_text,
        linkedin_url=compiled.linkedin_url,
        structured_constraints=compiled.structured_constraints,
        deterministic_filters={
            "titles": compiled.deterministic_filters.titles,
            "locations": compiled.deterministic_filters.locations,
            "remote": compiled.deterministic_filters.remote,
            "workplace_types": compiled.deterministic_filters.workplace_types,
            "employment_types": compiled.deterministic_filters.employment_types,
            "seniority": compiled.deterministic_filters.seniority,
            "companies": compiled.deterministic_filters.companies,
            "posted_within_days": compiled.deterministic_filters.posted_within_days,
            "exclude_keywords": compiled.deterministic_filters.exclude_keywords,
            "easy_apply": compiled.deterministic_filters.easy_apply,
            "under10_applicants": compiled.deterministic_filters.under10_applicants,
        },
        ai_constraints=compiled.ai_constraints,
        unsupported_constraints=compiled.unsupported_constraints,
    )


@app.get("/api/v1/providers/apify/health", tags=["provider"])
async def apify_health() -> dict[str, object]:
    return await _apify_adapter().health_check()


@app.post("/api/v1/providers/apify/search", response_model=ProviderSearchResponse, tags=["provider"])
async def search_with_apify(payload: SearchQueryInput) -> ProviderSearchResponse:
    compiled = compiler.compile(SearchQuery(**payload.model_dump()))
    provider_config = dict(compiled.structured_constraints)
    provider_config["rows"] = settings.apify_default_rows
    provider_config["source_url"] = (
        compiled.linkedin_url
        if payload.source_url and "source_url" not in compiled.unsupported_constraints
        else None
    )
    provider_config["exclude_keywords"] = compiled.deterministic_filters.exclude_keywords

    try:
        candidates = await _apify_adapter().search(
            JobSearchInput(
                search_text=compiled.search_text,
                provider_config=provider_config,
            )
        )
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ProviderSearchResponse(
        provider="apify-linkedin",
        count=len(candidates),
        candidates=[
            JobCandidateResponse(
                source=c.source,
                source_job_id=c.source_job_id,
                job_url=c.job_url,
                title=c.title,
                company_name=c.company_name,
                location=c.location,
                posted_text=c.posted_text,
                provenance=c.provenance or {},
            )
            for c in candidates
        ],
    )


@app.post("/api/v1/providers/apify/details", response_model=JobDetailResponse, tags=["provider"])
async def detail_with_apify(payload: JobDetailRequest) -> JobDetailResponse:
    try:
        result = await _apify_adapter().get_job_details(
            JobDetailInput(
                source_job_id=payload.source_job_id,
                job_url=payload.job_url,
            )
        )
        canonical = detail_extractor.extract(result.raw, provenance=result.provenance)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return JobDetailResponse.model_validate(asdict(canonical))


@app.post(
    "/api/v1/jobs/import",
    response_model=JobImportResponse,
    tags=["jobs"],
)
async def import_job(
    payload: JobImportRequest,
    session: Session = db_dependency,
) -> JobImportResponse:
    search_run_id = None
    if payload.search_run_id:
        try:
            search_run_id = UUID(payload.search_run_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid search_run_id") from exc

    service = ApifyJobImportService(session, _apify_adapter())
    try:
        result = await service.import_job(
            JobDetailInput(
                source_job_id=payload.source_job_id,
                job_url=payload.job_url,
            ),
            search_run_id=search_run_id,
            discovered_from=payload.discovered_from,
        )
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ProviderError as exc:
        session.rollback()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="job persistence failed") from exc

    return JobImportResponse(
        job_id=str(result.job.id),
        source=result.job.source,
        source_job_id=result.job.source_job_id,
        title=result.job.title,
        created=result.created,
        deduplicated=result.deduplicated,
        snapshot_created=result.snapshot_created,
        company_created=result.company_created,
    )





def _candidate_profile_response(
    result: CandidateProfileResult,
    *,
    saved: bool = False,
) -> CandidateProfileResponse:
    profile = CandidateProfileInput.model_validate(asdict(result.data))
    payload = {
        "user_id": result.user_id,
        "profile_id": result.profile_id,
        "exists": result.exists,
        "profile": profile,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
    }
    if saved:
        return CandidateProfileUpdateResponse(**payload, saved=True)
    return CandidateProfileResponse(**payload)


@app.get(
    "/api/v1/profile",
    response_model=CandidateProfileResponse,
    tags=["candidate-profile"],
)
def get_candidate_profile(session: Session = db_dependency) -> CandidateProfileResponse:
    user_id = UUID(settings.default_user_id)
    result = CandidateProfileService(session).get(user_id)
    return _candidate_profile_response(result)


@app.put(
    "/api/v1/profile",
    response_model=CandidateProfileUpdateResponse,
    tags=["candidate-profile"],
)
def update_candidate_profile(
    payload: CandidateProfileInput,
    session: Session = db_dependency,
) -> CandidateProfileUpdateResponse:
    user_id = UUID(settings.default_user_id)
    data = CandidateProfileData(
        full_name=payload.full_name,
        headline=payload.headline,
        summary=payload.summary,
        target_titles=payload.target_titles,
        skills=payload.skills,
        technologies=payload.technologies,
        certifications=payload.certifications,
        education=payload.education,
        languages=payload.languages,
        industries=payload.industries,
        preferred_locations=payload.preferred_locations,
        preferred_countries=payload.preferred_countries,
        workplace_types=payload.workplace_types,
        employment_types=payload.employment_types,
        seniority=payload.seniority,
        preferred_companies=payload.preferred_companies,
        excluded_companies=payload.excluded_companies,
        excluded_keywords=payload.excluded_keywords,
        min_salary=str(payload.min_salary) if payload.min_salary is not None else None,
        salary_currency=payload.salary_currency,
        years_experience=(
            str(payload.years_experience) if payload.years_experience is not None else None
        ),
        willing_to_relocate=payload.willing_to_relocate,
    )
    try:
        result = CandidateProfileService(session).upsert(user_id, data)
        session.commit()
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="candidate profile save failed") from exc
    return _candidate_profile_response(result, saved=True)

@app.get(
    "/api/v1/dashboard/overview",
    response_model=DashboardOverviewResponse,
    tags=["dashboard"],
)
def dashboard_overview(session: Session = db_dependency) -> DashboardOverviewResponse:
    overview = DashboardService(session).overview()
    return DashboardOverviewResponse(**asdict(overview))


@app.get(
    "/api/v1/dashboard/jobs",
    response_model=DashboardJobsResponse,
    tags=["dashboard"],
)
def dashboard_jobs(
    offset: int = 0,
    limit: int = 50,
    query: str | None = None,
    state: str | None = None,
    remote_only: bool = False,
    country_code: str | None = None,
    session: Session = db_dependency,
) -> DashboardJobsResponse:
    if offset < 0:
        raise HTTPException(status_code=422, detail="offset must be >= 0")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")

    total, jobs = DashboardService(session).list_jobs(
        offset=offset,
        limit=limit,
        query=query,
        state=state,
        remote_only=remote_only,
        country_code=country_code,
    )
    return DashboardJobsResponse(
        total=total,
        offset=offset,
        limit=limit,
        jobs=[DashboardJobResponse(**asdict(job)) for job in jobs],
    )


@app.get(
    "/api/v1/dashboard/search-runs",
    response_model=DashboardSearchRunsResponse,
    tags=["dashboard"],
)
def dashboard_search_runs(
    limit: int = 10,
    session: Session = db_dependency,
) -> DashboardSearchRunsResponse:
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 50")

    runs = DashboardService(session).recent_search_runs(limit=limit)
    return DashboardSearchRunsResponse(
        runs=[DashboardSearchRunResponse(**asdict(run)) for run in runs],
    )
