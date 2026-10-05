from datetime import datetime, timezone
from decimal import Decimal

import pytest

from apps.api.app.domain.detail import JobDetailExtractor
from apps.api.app.domain.detail_utils import detect_ats, parse_posted_at


def test_extracts_current_actor_detail_shape() -> None:
    captured = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    raw = {
        "id": "4459772101",
        "title": "Senior Software Engineer",
        "jobUrl": "https://www.linkedin.com/jobs/view/4459772101",
        "companyName": "Example GmbH",
        "companyUrl": "https://www.linkedin.com/company/example",
        "companyWebsite": "https://example.com/",
        "companyId": "1234567",
        "companyLogo": "https://example.com/logo.png",
        "companyEmployeeCount": 2400,
        "companyFollowerCount": 51200,
        "companyIndustries": "Software Development",
        "companyDescription": "Example company",
        "location": "Berlin, Germany",
        "locationParsed": {
            "city": "Berlin",
            "region": "Berlin",
            "country": "DE",
            "formatted": "Berlin, Germany",
        },
        "workType": "Remote",
        "contractType": "Full-time",
        "experienceLevel": "Mid-Senior level",
        "jobFunction": "Engineering and Information Technology",
        "sector": "Software Development",
        "salary": "€70,000 - €90,000 per year",
        "salaryMin": 70000,
        "salaryMax": 90000,
        "salaryCurrency": "EUR",
        "salaryPeriod": "year",
        "applicationsCount": "27 applicants",
        "postedTime": "3 days ago",
        "publishedAt": "2026-08-29",
        "postedAtTimestamp": 1788000000000,
        "benefits": "Medical, Vision, 401k",
        "applyType": "EXTERNAL",
        "applyUrl": "https://boards.greenhouse.io/example/jobs/123",
        "description": "Build software for the team.",
        "jobState": "LISTED",
        "repostedJob": True,
        "verified": True,
        "posterFullName": "Recruiter",
        "scrapingInfo": {"page": 1, "index": 3},
    }

    job = JobDetailExtractor().extract(
        raw,
        provenance={"provider": "apify-linkedin"},
        captured_at=captured,
    )

    assert job.source_id == "4459772101"
    assert job.title == "Senior Software Engineer"
    assert job.normalized_title == "senior software engineer"
    assert job.city == "Berlin"
    assert job.country_code == "DE"
    assert job.workplace_type == "REMOTE"
    assert job.remote_allowed is True
    assert job.salary_min == Decimal("70000")
    assert job.salary_max == Decimal("90000")
    assert job.salary_currency == "EUR"
    assert job.applicant_count == 27
    assert job.external_apply_url == "https://boards.greenhouse.io/example/jobs/123"
    assert job.ats_provider == "greenhouse"
    assert job.state == "ACTIVE"
    assert job.reposted is True
    assert job.company is not None
    assert job.company.employee_count == 2400
    assert job.signals["verified"] is True
    assert job.provenance["provider"] == "apify-linkedin"


def test_relative_posted_time_fallback() -> None:
    captured = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)

    posted_at, precision = parse_posted_at(
        None,
        None,
        "2 days ago",
        captured,
    )

    assert posted_at == datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
    assert precision == "day"


def test_ats_detection() -> None:
    assert detect_ats("https://jobs.ashbyhq.com/example/123") == "ashby"
    assert detect_ats("https://example.com/jobs/123") is None


def test_missing_job_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        JobDetailExtractor().extract({"title": "Software Engineer"})


def test_salary_fallback() -> None:
    job = JobDetailExtractor().extract(
        {
            "id": "1",
            "title": "Developer",
            "salary": "$70k - $90k",
            "applyType": "EXTERNAL",
            "applyUrl": "https://jobs.lever.co/example/1",
        }
    )

    assert job.salary_min == Decimal("70000")
    assert job.salary_max == Decimal("90000")
    assert job.ats_provider == "lever"
