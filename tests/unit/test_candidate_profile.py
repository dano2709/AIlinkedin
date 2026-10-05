from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from apps.api.app.main import app, get_db
from apps.api.app.services.candidate_profile import (
    CandidateProfileData,
    CandidateProfileResult,
    normalize_profile,
)


def sample_data() -> CandidateProfileData:
    return CandidateProfileData(
        full_name=" Daniel   Test ",
        headline=" Python Engineer ",
        summary=" Profile summary ",
        target_titles=["Python Engineer", "python engineer", "Backend Developer"],
        skills=["Python", " python ", "SQL"],
        technologies=["FastAPI"],
        certifications=[],
        education=["MSc"],
        languages=["Czech"],
        industries=["Software"],
        preferred_locations=["Prague"],
        preferred_countries=["CZ"],
        workplace_types=["REMOTE"],
        employment_types=["FULL_TIME"],
        seniority=["MID"],
        preferred_companies=["Example"],
        excluded_companies=[],
        excluded_keywords=["crypto"],
        min_salary="70000",
        salary_currency="czk",
        years_experience="5",
        willing_to_relocate=True,
    )


def test_profile_normalization_deduplicates_lists() -> None:
    normalized = normalize_profile(sample_data())

    assert normalized.full_name == "Daniel Test"
    assert normalized.target_titles == ["Python Engineer", "Backend Developer"]
    assert normalized.skills == ["Python", "SQL"]
    assert normalized.salary_currency == "CZK"


class FakeProfileService:
    def __init__(self, session: Any) -> None:
        self.data = sample_data()
        self.user_id = uuid4()
        self.profile_id = uuid4()

    def get(self, user_id: Any) -> CandidateProfileResult:
        return CandidateProfileResult(
            user_id=user_id,
            profile_id=self.profile_id,
            data=self.data,
            exists=True,
            created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
        )

    def upsert(self, user_id: Any, data: CandidateProfileData) -> CandidateProfileResult:
        self.data = normalize_profile(data)
        return CandidateProfileResult(
            user_id=user_id,
            profile_id=self.profile_id,
            data=self.data,
            exists=True,
            created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
        )


def test_profile_endpoints(monkeypatch: Any) -> None:
    monkeypatch.setattr("apps.api.app.main.CandidateProfileService", FakeProfileService)

    def fake_db() -> Any:
        yield MagicMock()

    app.dependency_overrides[get_db] = fake_db
    try:
        response = TestClient(app).get("/api/v1/profile")

        assert response.status_code == 200
        body = response.json()
        assert body["exists"] is True
        assert body["profile"]["salary_currency"] == "CZK"

        response = TestClient(app).put(
            "/api/v1/profile",
            json={
                "full_name": " Daniel   Test ",
                "target_titles": ["Python Engineer", "python engineer"],
                "skills": ["Python", " python "],
                "salary_currency": "czk",
                "willing_to_relocate": True,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["saved"] is True
        assert body["profile"]["full_name"] == "Daniel Test"
        assert body["profile"]["target_titles"] == ["Python Engineer"]
        assert body["profile"]["salary_currency"] == "CZK"
    finally:
        app.dependency_overrides.clear()
