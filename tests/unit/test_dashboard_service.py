from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from apps.api.app.domain.detail import CanonicalRecord
from apps.api.app.models import Company, JobState, WorkplaceType
from apps.api.app.services.dashboard import DashboardService


def test_overview_aggregates_dashboard_counts() -> None:
    session = MagicMock()
    session.scalar.side_effect = [12, 8, 5, 3, 4, 2]

    overview = DashboardService(session).overview()

    assert overview.total_jobs == 12
    assert overview.active_jobs == 8
    assert overview.remote_jobs == 5
    assert overview.new_jobs_24h == 3
    assert overview.companies == 4
    assert overview.searches == 2
    assert session.scalar.call_count == 6


def test_job_projection_keeps_dashboard_fields() -> None:
    company = SimpleNamespace(name="Example")
    job = SimpleNamespace(
        id="job-id",
        source="linkedin",
        source_job_id="123",
        title="Python Developer",
        company=company,
        location_raw="Prague, Czechia",
        country_code="CZ",
        workplace_type=WorkplaceType.REMOTE,
        employment_type="Full-time",
        experience_level="Mid-Senior level",
        salary_min=Decimal("70000"),
        salary_max=Decimal("90000"),
        salary_currency="CZK",
        job_state=JobState.ACTIVE,
        applicant_count=7,
        apply_url="https://www.linkedin.com/jobs/view/123",
        external_apply_url="https://jobs.example.com/123",
        ats_provider="lever",
        posted_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        discovered_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
    )

    projected = DashboardService(MagicMock())._job(job)

    assert projected.title == "Python Developer"
    assert projected.company_name == "Example"
    assert projected.workplace_type == "REMOTE"
    assert projected.salary_min == "70000"
    assert projected.applicant_count == 7
