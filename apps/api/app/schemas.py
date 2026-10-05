from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchQueryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titles: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    remote: bool | None = None
    workplace_types: list[str] = Field(default_factory=list)
    employment_types: list[str] = Field(default_factory=list)
    seniority: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    posted_within_days: int | None = Field(default=None, ge=0, le=365)
    exclude_keywords: list[str] = Field(default_factory=list)
    easy_apply: bool | None = None
    under10_applicants: bool | None = None
    natural_language_query: str | None = None
    source_url: str | None = None

    @field_validator(
        "titles",
        "keywords",
        "locations",
        "workplace_types",
        "employment_types",
        "seniority",
        "companies",
        "exclude_keywords",
    )
    @classmethod
    def clean_list(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]


class CompiledSearchResponse(BaseModel):
    search_text: str
    linkedin_url: str | None
    structured_constraints: dict[str, Any]
    deterministic_filters: dict[str, Any]
    ai_constraints: dict[str, Any]
    unsupported_constraints: list[str]


class JobCandidateResponse(BaseModel):
    source: str
    source_job_id: str
    job_url: str
    title: str | None
    company_name: str | None
    location: str | None
    posted_text: str | None
    provenance: dict[str, Any]


class ProviderSearchResponse(BaseModel):
    provider: str
    count: int
    candidates: list[JobCandidateResponse]
