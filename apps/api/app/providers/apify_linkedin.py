from __future__ import annotations

from typing import Any

import httpx

from ..domain.providers import (
    JobDetailInput,
    JobDetailResult,
    JobSearchCandidate,
    JobSearchInput,
)


class ProviderError(RuntimeError):
    pass


class ApifyLinkedInAdapter:
    """
    Apify-backed LinkedIn Jobs adapter.

    The provider-specific input/output mapping lives here. The rest of the
    application only consumes canonical provider-neutral objects.
    """

    name = "apify-linkedin"

    def __init__(
        self,
        token: str,
        actor_id: str = "bebity/linkedin-jobs-scraper",
        base_url: str = "https://api.apify.com/v2",
        timeout_seconds: float = 180.0,
    ) -> None:
        if not token:
            raise ValueError("Apify token is required")
        self.token = token
        self.actor_id = actor_id
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def search(self, query: JobSearchInput) -> list[JobSearchCandidate]:
        payload = self._build_search_payload(query)
        rows = await self._run_actor(payload)
        return [self._to_candidate(row, query.search_text) for row in rows if self._is_job_row(row)]

    async def get_job_details(self, job: JobDetailInput) -> JobDetailResult:
        if not job.job_url and not job.source_job_id:
            raise ValueError("job_url or source_job_id is required")

        url = job.job_url or f"https://www.linkedin.com/jobs/view/{job.source_job_id}/"
        payload = {
            "startUrls": [url],
            "maxRowsPerUrl": 1,
            "companyProfile": True,
            "enrichCompany": True,
        }
        rows = await self._run_actor(payload)
        if not rows:
            raise ProviderError("Apify returned no job details")

        return JobDetailResult(
            raw=rows[0],
            provenance={
                "provider": self.name,
                "actor_id": self.actor_id,
                "source_url": url,
            },
        )

    async def health_check(self) -> dict[str, Any]:
        url = f"{self.base_url}/acts/{self._actor_path()}"
        params = {"token": self.token}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            return {"status": "unhealthy", "provider": self.name, "error": str(exc)}

        return {"status": "healthy", "provider": self.name, "actor_id": self.actor_id}

    async def _run_actor(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        url = (
            f"{self.base_url}/acts/{self._actor_path()}/"
            "run-sync-get-dataset-items"
        )
        params = {"token": self.token}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, params=params, json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ProviderError("Apify request timed out") from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise ProviderError(
                f"Apify request failed with HTTP {exc.response.status_code}: {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Apify request failed: {exc}") from exc

        data = response.json()
        if not isinstance(data, list):
            raise ProviderError("Apify returned an unexpected dataset response")
        return [row for row in data if isinstance(row, dict)]

    def _actor_path(self) -> str:
        return self.actor_id.replace("/", "~", 1)

    def _build_search_payload(self, query: JobSearchInput) -> dict[str, Any]:
        config = query.provider_config
        if config.get("source_url"):
            return {
                "startUrls": [config["source_url"]],
                "maxRowsPerUrl": int(config.get("rows", 25)),
                "companyProfile": bool(config.get("company_profile", True)),
                "enrichCompany": bool(config.get("enrich_company", False)),
            }

        payload: dict[str, Any] = {
            "rows": int(config.get("rows", 25)),
            "companyProfile": bool(config.get("company_profile", True)),
            "enrichCompany": bool(config.get("enrich_company", False)),
        }

        if config.get("titles"):
            payload["titles"] = config["titles"]
        if config.get("locations"):
            payload["locations"] = config["locations"]
        if config.get("company_names"):
            payload["companyName"] = config["company_names"][0]
        if config.get("easy_apply") is True:
            payload["easyApply"] = True
        if config.get("under10_applicants") is True:
            payload["under10Applicants"] = True

        workplace_types = [str(value).upper() for value in config.get("workplace_types", [])]
        work_type_map = {"ON_SITE": "1", "REMOTE": "2", "HYBRID": "3"}
        mapped_work_types = [
            work_type_map[value] for value in workplace_types if value in work_type_map
        ]
        if mapped_work_types:
            payload["workTypes"] = mapped_work_types

        published = self._published_at_value(config.get("posted_within_days"))
        if published:
            payload["publishedAt"] = published

        contract_types = self._normalize_contract_types(config.get("employment_types", []))
        if contract_types:
            payload["contractTypes"] = contract_types

        experience_levels = self._normalize_experience_levels(config.get("seniority", []))
        if experience_levels:
            payload["experienceLevels"] = experience_levels

        if query.search_text and not payload.get("titles"):
            payload["titles"] = [query.search_text]

        return payload

    @staticmethod
    def _published_at_value(days: int | None) -> str | None:
        if days is None:
            return None
        if days <= 1:
            return "r86400"
        if days <= 7:
            return "r604800"
        return "r2592000"

    @staticmethod
    def _normalize_contract_types(values: list[str]) -> list[str]:
        mapping = {
            "FULL_TIME": "Full-time",
            "PART_TIME": "Part-time",
            "CONTRACT": "Contract",
            "TEMPORARY": "Temporary",
            "INTERNSHIP": "Internship",
            "VOLUNTEER": "Volunteer",
        }
        return [mapping[value.upper()] for value in values if value.upper() in mapping]

    @staticmethod
    def _normalize_experience_levels(values: list[str]) -> list[str]:
        mapping = {
            "INTERNSHIP": "Internship",
            "ENTRY": "Entry level",
            "ENTRY_LEVEL": "Entry level",
            "ASSOCIATE": "Associate",
            "MID": "Mid-Senior level",
            "MID_SENIOR": "Mid-Senior level",
            "SENIOR": "Mid-Senior level",
            "DIRECTOR": "Director",
            "EXECUTIVE": "Executive",
        }
        return list(dict.fromkeys(mapping[value.upper()] for value in values if value.upper() in mapping))

    @staticmethod
    def _is_job_row(row: dict[str, Any]) -> bool:
        return bool(row.get("id") or row.get("jobUrl"))

    @staticmethod
    def _to_candidate(row: dict[str, Any], search_text: str) -> JobSearchCandidate:
        job_id = str(row.get("id") or "").strip()
        job_url = str(row.get("jobUrl") or "").strip()
        if not job_url and job_id:
            job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"

        scraping_info = row.get("scrapingInfo")
        provenance = scraping_info if isinstance(scraping_info, dict) else {}
        provenance = {
            **provenance,
            "provider": "apify-linkedin",
            "search_text": search_text,
        }

        return JobSearchCandidate(
            source="linkedin",
            source_job_id=job_id,
            job_url=job_url,
            title=row.get("title"),
            company_name=row.get("companyName"),
            location=row.get("location"),
            posted_text=row.get("postedTime"),
            provenance=provenance,
        )
