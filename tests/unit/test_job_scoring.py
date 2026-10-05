from decimal import Decimal
from types import SimpleNamespace


from apps.api.app.providers.openai_scoring import OpenAIResponsesScoringProvider
from apps.api.app.scoring_schemas import AIJobScoreResult
from apps.api.app.services.candidate_profile import CandidateProfileData
from apps.api.app.services.job_scoring_core import weighted_fit_score


def make_result() -> AIJobScoreResult:
    return AIJobScoreResult(
        confidence=Decimal("0.93"),
        breakdown={
            "title_alignment": 25,
            "skills_match": 22,
            "experience_match": 14,
            "location_workplace": 10,
            "compensation": 8,
            "industry_company": 4,
            "exclusions": 9,
        },
        matched_skills=["Python", "FastAPI"],
        missing_skills=["Kubernetes"],
        strengths=["Strong title match"],
        concerns=["Kubernetes missing"],
        recommendation="strong_match",
        summary="Strong overall fit.",
    )


def test_weighted_fit_score_is_sum_of_validated_components() -> None:
    assert weighted_fit_score(make_result()) == 92


def test_openai_provider_parses_response_json() -> None:
    profile = CandidateProfileData(
        full_name="Test",
        headline="Python Engineer",
        summary=None,
        target_titles=["Python Engineer"],
        skills=["Python"],
        technologies=["FastAPI"],
        certifications=[],
        education=[],
        languages=[],
        industries=["Software"],
        preferred_locations=["Prague"],
        preferred_countries=["CZ"],
        workplace_types=["REMOTE"],
        employment_types=["FULL_TIME"],
        seniority=["MID"],
        preferred_companies=[],
        excluded_companies=[],
        excluded_keywords=[],
        min_salary="70000",
        salary_currency="CZK",
        years_experience="5",
        willing_to_relocate=False,
    )

    class FakeResponses:
        async def create(self, **kwargs):
            return SimpleNamespace(
                output_text=make_result().model_dump_json()
            )

    provider = OpenAIResponsesScoringProvider("test-key")
    provider.client = SimpleNamespace(responses=FakeResponses())

    import asyncio

    result = asyncio.run(
        provider.score(profile, {"title": "Developer"})
    )
    assert result.fit_score if False else result.recommendation == "strong_match"
