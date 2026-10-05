from fastapi import FastAPI

from .domain import SearchQuery, SearchQueryCompiler
from .schemas import CompiledSearchResponse, SearchQueryInput
from .settings import settings

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="LinkedIn Job Intelligence API",
)

compiler = SearchQueryCompiler()


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/api/v1/meta", tags=["system"])
def meta() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": "0.2.0",
        "status": "phase-2",
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
            "employment_types": compiled.deterministic_filters.employment_types,
            "seniority": compiled.deterministic_filters.seniority,
            "companies": compiled.deterministic_filters.companies,
            "posted_within_days": compiled.deterministic_filters.posted_within_days,
            "exclude_keywords": compiled.deterministic_filters.exclude_keywords,
        },
        ai_constraints=compiled.ai_constraints,
        unsupported_constraints=compiled.unsupported_constraints,
    )
