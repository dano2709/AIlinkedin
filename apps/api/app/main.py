from dataclasses import asdict

from fastapi import FastAPI, HTTPException

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
    ProviderSearchResponse,
    SearchQueryInput,
)
from .settings import settings

app = FastAPI(
    title=settings.app_name,
    version="0.4.0",
    description="LinkedIn Job Intelligence API",
)

compiler = SearchQueryCompiler()
detail_extractor = JobDetailExtractor()


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
        "version": "0.4.0",
        "status": "phase-4",
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
    adapter = _apify_adapter()
    return await adapter.health_check()


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


@app.post(
    "/api/v1/providers/apify/details",
    response_model=JobDetailResponse,
    tags=["provider"],
)
async def detail_with_apify(payload: JobDetailRequest) -> JobDetailResponse:
    try:
        result = await _apify_adapter().get_job_details(
            JobDetailInput(
                source_job_id=payload.source_job_id,
                job_url=payload.job_url,
            )
        )
        canonical = detail_extractor.extract(
            result.raw,
            provenance=result.provenance,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return JobDetailResponse.model_validate(asdict(canonical))
