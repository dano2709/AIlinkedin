from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CandidateProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, max_length=200)
    headline: str | None = Field(default=None, max_length=300)
    summary: str | None = Field(default=None, max_length=5000)
    target_titles: list[str] = Field(default_factory=list, max_length=30)
    skills: list[str] = Field(default_factory=list, max_length=100)
    technologies: list[str] = Field(default_factory=list, max_length=100)
    certifications: list[str] = Field(default_factory=list, max_length=50)
    education: list[str] = Field(default_factory=list, max_length=50)
    languages: list[str] = Field(default_factory=list, max_length=30)
    industries: list[str] = Field(default_factory=list, max_length=50)
    preferred_locations: list[str] = Field(default_factory=list, max_length=50)
    preferred_countries: list[str] = Field(default_factory=list, max_length=30)
    workplace_types: list[str] = Field(default_factory=list, max_length=10)
    employment_types: list[str] = Field(default_factory=list, max_length=10)
    seniority: list[str] = Field(default_factory=list, max_length=10)
    preferred_companies: list[str] = Field(default_factory=list, max_length=50)
    excluded_companies: list[str] = Field(default_factory=list, max_length=50)
    excluded_keywords: list[str] = Field(default_factory=list, max_length=100)
    min_salary: Decimal | None = Field(default=None, ge=0)
    salary_currency: str | None = Field(default=None, min_length=3, max_length=3)
    years_experience: Decimal | None = Field(default=None, ge=0, le=80)
    willing_to_relocate: bool = False

    @field_validator(
        "target_titles",
        "skills",
        "technologies",
        "certifications",
        "education",
        "languages",
        "industries",
        "preferred_locations",
        "preferred_countries",
        "workplace_types",
        "employment_types",
        "seniority",
        "preferred_companies",
        "excluded_companies",
        "excluded_keywords",
    )
    @classmethod
    def clean_lists(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]

    @field_validator("salary_currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper().strip() if value else None


class CandidateProfileResponse(BaseModel):
    user_id: UUID
    profile_id: UUID | None
    exists: bool
    profile: CandidateProfileInput
    created_at: datetime | None
    updated_at: datetime | None


class CandidateProfileUpdateResponse(CandidateProfileResponse):
    saved: bool
