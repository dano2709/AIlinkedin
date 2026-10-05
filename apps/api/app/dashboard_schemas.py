from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DashboardOverviewResponse(BaseModel):
    total_jobs: int
    active_jobs: int
    remote_jobs: int
    new_jobs_24h: int
    companies: int
    searches: int


class DashboardJobResponse(BaseModel):
    id: str
    source: str
    source_job_id: str
    title: str
    company_name: str | None
    location: str | None
    country_code: str | None
    workplace_type: str
    employment_type: str | None
    experience_level: str | None
    salary_min: str | None
    salary_max: str | None
    salary_currency: str | None
    job_state: str
    applicant_count: int | None
    apply_url: str | None
    external_apply_url: str | None
    ats_provider: str | None
    posted_at: datetime | None
    discovered_at: datetime


class DashboardJobsResponse(BaseModel):
    total: int
    offset: int
    limit: int
    jobs: list[DashboardJobResponse]


class DashboardSearchRunResponse(BaseModel):
    id: str
    search_name: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class DashboardSearchRunsResponse(BaseModel):
    runs: list[DashboardSearchRunResponse]
