import pytest

from apps.api.app.domain.providers import JobDetailInput, JobSearchInput
from apps.api.app.providers.apify_linkedin import ApifyLinkedInAdapter


def test_builds_current_filter_payload() -> None:
    adapter = ApifyLinkedInAdapter(token="test")
    payload = adapter._build_search_payload(
        JobSearchInput(
            search_text="Python Developer",
            provider_config={
                "titles": ["Python Developer"],
                "locations": ["Prague"],
                "workplace_types": ["REMOTE", "HYBRID"],
                "employment_types": ["FULL_TIME"],
                "seniority": ["MID"],
                "posted_within_days": 7,
                "easy_apply": True,
                "under10_applicants": True,
                "rows": 25,
            },
        )
    )

    assert payload["titles"] == ["Python Developer"]
    assert payload["locations"] == ["Prague"]
    assert payload["workTypes"] == ["2", "3"]
    assert payload["contractTypes"] == ["Full-time"]
    assert payload["experienceLevels"] == ["Mid-Senior level"]
    assert payload["publishedAt"] == "r604800"
    assert payload["easyApply"] is True
    assert payload["under10Applicants"] is True


def test_remote_flag_maps_to_provider_work_type() -> None:
    adapter = ApifyLinkedInAdapter(token="test")
    payload = adapter._build_search_payload(
        JobSearchInput(
            search_text="Python Developer",
            provider_config={"remote": True, "rows": 10},
        )
    )

    assert payload["workTypes"] == ["2"]


def test_maps_actor_row_to_candidate() -> None:
    adapter = ApifyLinkedInAdapter(token="test")
    candidate = adapter._to_candidate(
        {
            "id": "123",
            "jobUrl": "https://www.linkedin.com/jobs/view/123/",
            "title": "Software Engineer",
            "companyName": "Example",
            "location": "Prague, Czechia",
            "postedTime": "1 day ago",
            "scrapingInfo": {"title": "Software Engineer", "location": "Prague"},
        },
        "Software Engineer",
    )

    assert candidate.source_job_id == "123"
    assert candidate.company_name == "Example"
    assert candidate.provenance["provider"] == "apify-linkedin"


def test_detail_requires_identifier() -> None:
    adapter = ApifyLinkedInAdapter(token="test")
    with pytest.raises(ValueError):
        import asyncio
        asyncio.run(adapter.get_job_details(JobDetailInput()))
