from apps.api.app.db import Base
from apps.api.app import models  # noqa: F401


def test_expected_tables_are_registered() -> None:
    expected = {
        "users",
        "candidate_profiles",
        "providers",
        "searches",
        "search_runs",
        "provider_runs",
        "companies",
        "jobs",
        "job_sources",
        "job_snapshots",
        "job_search_matches",
        "skills",
        "job_skills",
        "job_ai_analyses",
        "candidate_job_scores",
        "applications",
        "application_events",
        "notifications",
        "notification_deliveries",
        "parser_versions",
        "system_events",
        "errors",
    }

    assert expected.issubset(Base.metadata.tables)
