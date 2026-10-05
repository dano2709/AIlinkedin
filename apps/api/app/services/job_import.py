from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from ..domain.detail import JobDetailExtractor
from ..domain.providers import JobDetailInput
from ..providers.apify_linkedin import ApifyLinkedInAdapter
from .job_persistence import JobPersistenceService, PersistenceResult


class ApifyJobImportService:
    def __init__(self, session: Session, adapter: ApifyLinkedInAdapter) -> None:
        self.persistence = JobPersistenceService(session)
        self.adapter = adapter
        self.extractor = JobDetailExtractor()

    async def import_job(
        self,
        job: JobDetailInput,
        *,
        search_run_id: UUID | None = None,
        discovered_from: str | None = None,
    ) -> PersistenceResult:
        result = await self.adapter.get_job_details(job)
        canonical = self.extractor.extract(result.raw, provenance=result.provenance)
        return self.persistence.upsert(
            canonical,
            search_run_id=search_run_id,
            discovered_from=discovered_from,
        )
