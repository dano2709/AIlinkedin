from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchQueryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titles: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    remote: bool | None = None
    employment_types: list[str] = Field(default_factory=list)
    seniority: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    posted_within_days: int | None = Field(default=None, ge=0, le=365)
    exclude_keywords: list[str] = Field(default_factory=list)
    natural_language_query: str | None = None
    source_url: str | None = None

    @field_validator(
        "titles",
        "keywords",
        "locations",
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
    structured_constraints: dict
    deterministic_filters: dict
    ai_constraints: dict
    unsupported_constraints: list[str]
