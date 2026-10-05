from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from apps.api.app.domain.detail import CanonicalCompany, CanonicalRecord
from apps.api.app.models import Company, Job
from apps.api.app.services.job_persistence import JobPersistenceService


def make_job(source_id: str = "123") -> CanonicalRecord:
    return CanonicalRecord(
        source="linkedin",
        source_id=source_id,
        url=f"https://www.linkedin.com/jobs/view/{source_id}",
        title="Python Developer",
        normalized_title="python developer",
        location_raw="Prague, Czechia",
        city="Prague",
        region="Prague",
        country="Czechia",
        country_code="CZ",
        workplace_type="REMOTE",
        remote_allowed=True,
        posted_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        posted_at_raw="2026-10-01",
        posted_at_precision="date",
        employment_type="Full-time",
        experience_level="Mid-Senior level",
        job_function="Engineering",
        industry="Software",
        salary_raw="70000-90000",
        salary_min=None,
        salary_max=None,
        salary_currency="CZK",
        salary_period="year",
        description="Build services.",
        responsibilities=[],
        requirements=["Python"],
        preferred_qualifications=[],
        benefits=[],
        skills=["Python"],
        technologies=["FastAPI"],
        certifications=[],
        education=[],
        languages=[],
        applicant_count=3,
        apply_type="EXTERNAL",
        apply_url="https://jobs.example.com/123",
        external_apply_url="https://jobs.example.com/123",
        ats_provider="lever",
        state="ACTIVE",
        reposted=False,
        scraped_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
        extractor_version="test",
        company=CanonicalCompany(
            source_company_id="c1",
            name="Example",
            url="https://www.linkedin.com/company/example",
            website="https://example.com",
            logo_url=None,
            employee_count=100,
            industry="Software",
        ),
        provenance={"provider": "apify-linkedin"},
        signals={},
    )


def test_upsert_creates_job_and_snapshot(monkeypatch) -> None:
    session = MagicMock()
    service = JobPersistenceService(session)
    company = Company(
        id=__import__("uuid").uuid4(),
        source="linkedin",
        source_company_id="c1",
        name="Example",
        normalized_name="example",
        enrichment={},
    )
    monkeypatch.setattr(service, "_upsert_company", lambda _: (company, True))
    monkeypatch.setattr(service, "_find_existing_job", lambda *_: None)
    monkeypatch.setattr(service, "_upsert_source", lambda *_: None)
    monkeypatch.setattr(service, "_create_snapshot_if_changed", lambda *args, **kwargs: True)

    result = service.upsert(make_job())

    assert result.created is True
    assert result.deduplicated is False
    assert result.snapshot_created is True
    assert result.company_created is True
    assert result.job.source_job_id == "123"
    assert session.flush.called
    assert session.add.called


def test_deduplication_preserves_existing_source_identity(monkeypatch) -> None:
    session = MagicMock()
    service = JobPersistenceService(session)
    company = Company(
        id=__import__("uuid").uuid4(),
        source="linkedin",
        source_company_id="c1",
        name="Example",
        normalized_name="example",
        enrichment={},
    )
    existing = Job(
        id=__import__("uuid").uuid4(),
        source="linkedin",
        source_job_id="old-id",
        canonical_url="https://www.linkedin.com/jobs/view/old-id",
        title="Old",
        normalized_title="old",
        location_raw=None,
        country_code=None,
        job_state="DISCOVERED",
        workplace_type="UNKNOWN",
        remote_allowed=False,
        reposted=False,
    )
    monkeypatch.setattr(service, "_upsert_company", lambda _: (company, False))
    monkeypatch.setattr(service, "_find_existing_job", lambda *_: existing)
    monkeypatch.setattr(service, "_last_snapshot_hashes", lambda _: None)
    monkeypatch.setattr(service, "_upsert_source", lambda *_: None)
    monkeypatch.setattr(service, "_create_snapshot_if_changed", lambda *args, **kwargs: True)

    result = service.upsert(make_job("new-id"))

    assert result.created is False
    assert result.deduplicated is True
    assert result.job.source_job_id == "old-id"
    assert result.job.title == "Python Developer"
