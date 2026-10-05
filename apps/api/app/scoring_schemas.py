from __future__ import annotations

from decimal import Decimal
from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    title_alignment: int = Field(ge=0, le=25)
    skills_match: int = Field(ge=0, le=25)
    experience_match: int = Field(ge=0, le=15)
    location_workplace: int = Field(ge=0, le=10)
    compensation: int = Field(ge=0, le=10)
    industry_company: int = Field(ge=0, le=5)
    exclusions: int = Field(ge=0, le=10)


class AIJobScoreResult(BaseModel):
    confidence: Decimal = Field(ge=0, le=1)
    breakdown: ScoreBreakdown
    matched_skills: list[str] = Field(default_factory=list, max_length=50)
    missing_skills: list[str] = Field(default_factory=list, max_length=50)
    strengths: list[str] = Field(default_factory=list, max_length=10)
    concerns: list[str] = Field(default_factory=list, max_length=10)
    recommendation: str = Field(min_length=1, max_length=40)
    summary: str = Field(min_length=1, max_length=1000)


class JobScoreResponse(BaseModel):
    job_id: str
    profile_id: str
    fit_score: int
    confidence: Decimal
    breakdown: ScoreBreakdown
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    concerns: list[str]
    recommendation: str
    summary: str
    model: str
    prompt_version: str
    created_at: str


class JobScoreRequest(BaseModel):
    force: bool = False
