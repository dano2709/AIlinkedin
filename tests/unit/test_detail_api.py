from typing import Any

from fastapi.testclient import TestClient

from apps.api.app.domain.providers import JobDetailResult
from apps.api.app.main import app


class FakeAdapter:
    async def get_job_details(self, job: Any) -> JobDetailResult:
        return JobDetailResult(
            raw={
                "id": "123",
                "title": "Python Developer",
                "jobUrl": "https://www.linkedin.com/jobs/view/123",
                "companyName": "Example",
                "location": "Prague, Czechia",
                "workType": "Hybrid",
                "contractType": "Full-time",
                "experienceLevel": "Mid-Senior level",
                "publishedAt": "2026-09-30",
                "salaryMin": 50000,
                "salaryMax": 70000,
                "salaryCurrency": "CZK",
                "salaryPeriod": "year",
                "applyType": "EXTERNAL",
                "applyUrl": "https://jobs.lever.co/example/123",
                "description": "Write Python services.",
            },
            provenance={"provider": "apify-linkedin", "actor_id": "bebity/linkedin-jobs-scraper"},
        )


def test_detail_endpoint_returns_canonical_job(monkeypatch: Any) -> None:
    monkeypatch.setattr("apps.api.app.main._apify_adapter", lambda: FakeAdapter())
    response = TestClient(app).post(
        "/api/v1/providers/apify/details",
        json={"source_job_id": "123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "linkedin"
    assert body["source_id"] == "123"
    assert body["workplace_type"] == "HYBRID"
    assert body["salary_min"] == "50000"
    assert body["ats_provider"] == "lever"
    assert body["provenance"]["provider"] == "apify-linkedin"


def test_detail_endpoint_requires_identifier() -> None:
    response = TestClient(app).post("/api/v1/providers/apify/details", json={})
    assert response.status_code == 422
