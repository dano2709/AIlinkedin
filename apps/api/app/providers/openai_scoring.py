from __future__ import annotations

from dataclasses import asdict
import json

from openai import AsyncOpenAI
from pydantic import ValidationError

from ..scoring_schemas import AIJobScoreResult
from ..services.candidate_profile import CandidateProfileData
from ..services.job_scoring_core import ScoringProviderError


class OpenAIResponsesScoringProvider:
    model = "gpt-6-luna"

    def __init__(self, api_key: str, *, model: str = "gpt-6-luna") -> None:
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def score(
        self,
        profile: CandidateProfileData,
        job_payload: dict[str, object],
    ) -> AIJobScoreResult:
        response = await self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You evaluate candidate-job fit. Return ONLY JSON. "
                                "Use only supplied evidence; unknown information is neutral."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": self._prompt(profile, job_payload),
                        }
                    ],
                },
            ],
            max_output_tokens=1200,
        )

        text = response.output_text
        if not text:
            raise ScoringProviderError("OpenAI returned no scoring output")

        try:
            return AIJobScoreResult.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ScoringProviderError("OpenAI returned invalid scoring JSON") from exc

    @staticmethod
    def _prompt(
        profile: CandidateProfileData,
        job: dict[str, object],
    ) -> str:
        return (
            "Score these exact categories: title_alignment 0-25; skills_match 0-25; "
            "experience_match 0-15; location_workplace 0-10; compensation 0-10; "
            "industry_company 0-5; exclusions 0-10. Total these yourself only for reasoning. "
            "Return keys: confidence, breakdown, matched_skills, missing_skills, strengths, "
            "concerns, recommendation, summary. recommendation must be one of "
            "strong_match, good_match, possible_match, weak_match. "
            "Do not invent candidate skills or experience.\n\n"
            f"PROFILE:\n{json.dumps(asdict(profile), ensure_ascii=False, default=str)}\n\n"
            f"JOB:\n{json.dumps(job, ensure_ascii=False, default=str)}"
        )
