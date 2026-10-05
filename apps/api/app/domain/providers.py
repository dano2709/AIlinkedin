from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class JobSearchInput:
    search_text: str
    provider_config: dict[str, Any]


@dataclass(slots=True)
class JobSearchCandidate:
    source: str
    source_job_id: str
    job_url: str
    title: str | None = None
    company_name: str | None = None
    location: str | None = None
    posted_text: str | None = None
    provenance: dict[str, Any] | None = None


@dataclass(slots=True)
class JobDetailInput:
    source_job_id: str | None = None
    job_url: str | None = None


@dataclass(slots=True)
class JobDetailResult:
    raw: dict[str, Any]
    provenance: dict[str, Any]


class JobSourceAdapter(Protocol):
    name: str

    async def search(self, query: JobSearchInput) -> list[JobSearchCandidate]:
        ...

    async def get_job_details(self, job: JobDetailInput) -> JobDetailResult:
        ...

    async def health_check(self) -> dict[str, Any]:
        ...
