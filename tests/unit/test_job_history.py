from datetime import datetime, timezone
from decimal import Decimal

from apps.api.app.domain.detail import CanonicalRecord
from apps.api.app.services.job_history import content_hash, dedupe_fingerprint, snapshot_hashes


def make_job() -> CanonicalRecord:
    return CanonicalRecord(
        source="linkedin",
        source_id="123",
        url="https://www.linkedin.com/jobs/view/123",
        title="Senior Python Engineer",
        normalized_title="senior python engineer",
        location_raw="Prague, Czechia",
        city="Prague",
        region="Prague",
        country="Czechia",
        country_code="CZ",
        workplace_type="HYBRID",
        remote_allowed=False,
        posted_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        posted_at_raw="2026-10-01",
        posted_at_precision="date",
        employment_type="Full-time",
        experience_level="Mid-Senior level",
        job_function="Engineering",
        industry="Software",
        salary_raw="80000-100000 CZK",
        salary_min=Decimal("80000"),
        salary_max=Decimal("100000"),
        salary_currency="CZK",
        salary_period="year",
        description="Build Python services.",
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
        ats_provider=None,
        state="ACTIVE",
        reposted=False,
        scraped_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
        extractor_version="test",
        company=None,
        provenance={},
        signals={},
    )


def test_snapshot_hashes_are_stable_and_sensitive_to_changes() -> None:
    job = make_job()
    first = snapshot_hashes(job)
    second = snapshot_hashes(job)
    assert first == second
    job.description = "Changed"
    assert snapshot_hashes(job)["description_hash"] != first["description_hash"]


def test_content_hash_is_stable() -> None:
    assert content_hash(["a", Decimal("1.0")]) == content_hash(["a", Decimal("1.0")])


def test_dedupe_fingerprint_changes_with_company_or_location() -> None:
    job = make_job()
    assert dedupe_fingerprint(job, "Example") != dedupe_fingerprint(job, "Other")
    other = make_job()
    other.city = "Brno"
    assert dedupe_fingerprint(job, "Example") != dedupe_fingerprint(other, "Example")
