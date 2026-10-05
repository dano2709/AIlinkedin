from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


class JobDetailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_job_id: str | None = None
    job_url: str | None = None

    @model_validator(mode="after")
    def require_identifier(self) -> JobDetailRequest:
        if not self.source_job_id and not self.job_url:
            raise ValueError("source_job_id or job_url is required")
        return self


class JobImportRequest(JobDetailRequest):
    search_run_id: str | None = None
    discovered_from: str | None = None


class JobImportResponse(BaseModel):
    job_id: str
    source: str
    source_job_id: str
    title: str
    created: bool
    deduplicated: bool
    snapshot_created: bool
    company_created: bool


class CompanyDetailResponse(BaseModel):
    source_company_id: str | None
    name: str | None
    url: str | None
    website: str | None
    logo_url: str | None
    employee_count: int | None
    industry: str | None
    industries: list[str]
    description: str | None
    tagline: str | None
    headquarters: dict[str, object]
    employee_size: str | None
    follower_count: int | None
    company_type: str | None
    founded_year: int | None
    enrichment: dict[str, object]


class JobDetailResponse(BaseModel):
    source: str
    source_id: str
    url: str
    title: str
    normalized_title: str
    location_raw: str | None
    city: str | None
    region: str | None
    country: str | None
    country_code: str | None
    workplace_type: str
    remote_allowed: bool
    posted_at: datetime | None
    posted_at_raw: str | None
    posted_at_precision: str | None
    employment_type: str | None
    experience_level: str | None
    job_function: str | None
    industry: str | None
    salary_raw: str | None
    salary_min: Decimal | None
    salary_max: Decimal | None
    salary_currency: str | None
    salary_period: str | None
    description: str | None
    responsibilities: list[str]
    requirements: list[str]
    preferred_qualifications: list[str]
    benefits: list[str]
    skills: list[str]
    technologies: list[str]
    certifications: list[str]
    education: list[str]
    languages: list[str]
    applicant_count: int | None
    apply_type: str | None
    apply_url: str | None
    external_apply_url: str | None
    ats_provider: str | None
    state: str
    reposted: bool
    scraped_at: datetime
    extractor_version: str
    company: CompanyDetailResponse | None
    provenance: dict[str, object]
    signals: dict[str, object]
