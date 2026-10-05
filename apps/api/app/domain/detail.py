from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping


EXTRACTOR_VERSION = "linkedin-bebity-v1"


@dataclass(slots=True)
class CanonicalRecord:
    source: str
    source_id: str
    url: str
    title: str
    normalized_title: str
    location_raw: str | None
    city: str | None
    region: str | None
    country: str | None
    country_code: str | None
    workplace_type: str
    remote_allowed: bool
    posted_at: datetime | None
    posted_at_raw: str | None
    posted_at_precision: str | None
    employment_type: str | None
    experience_level: str | None
    job_function: str | None
    industry: str | None
    salary_raw: str | None
    salary_min: Decimal | None
    salary_max: Decimal | None
    salary_currency: str | None
    salary_period: str | None
    description: str | None
    benefits: list[str]
    applicant_count: int | None
    apply_type: str | None
    apply_url: str | None
    external_apply_url: str | None
    ats_provider: str | None
    state: str
    reposted: bool
    scraped_at: datetime
    extractor_version: str
    company: dict[str, object]
    provenance: dict[str, object]
    signals: dict[str, object]


def extract_record(
    raw: Mapping[str, Any],
    *,
    provenance: Mapping[str, Any] | None = None,
    captured_at: datetime | None = None,
) -> CanonicalRecord:
    captured = captured_at or datetime.now(timezone.utc)
    source_id = str(raw.get("id") or "").strip()
    if not source_id:
        raise ValueError("detail payload is missing id")
    title = str(raw.get("title") or "Untitled job").strip()
    url = str(raw.get("jobUrl") or "").strip()
    return CanonicalRecord(
        source="linkedin",
        source_id=source_id,
        url=url,
        title=title,
        normalized_title=title.casefold(),
        location_raw=_text(raw.get("location")),
        city=None,
        region=None,
        country=None,
        country_code=None,
        workplace_type=_workplace(raw.get("workType")),
        remote_allowed=_workplace(raw.get("workType")) == "REMOTE",
        posted_at=None,
        posted_at_raw=_text(raw.get("publishedAt")) or _text(raw.get("postedTime")),
        posted_at_precision=None,
        employment_type=_text(raw.get("contractType")),
        experience_level=_text(raw.get("experienceLevel")),
        job_function=_text(raw.get("jobFunction")),
        industry=_text(raw.get("sector")),
        salary_raw=_text(raw.get("salary")),
        salary_min=_decimal(raw.get("salaryMin")),
        salary_max=_decimal(raw.get("salaryMax")),
        salary_currency=_text(raw.get("salaryCurrency")),
        salary_period=_text(raw.get("salaryPeriod")),
        description=_text(raw.get("description")),
        benefits=_list(raw.get("benefits")),
        applicant_count=_integer(raw.get("applicationsCount")),
        apply_type=_text(raw.get("applyType")),
        apply_url=_text(raw.get("applyUrl")),
        external_apply_url=_text(raw.get("applyUrl")) if str(raw.get("applyType") or "").upper() == "EXTERNAL" else None,
        ats_provider=None,
        state=_state(raw.get("jobState")),
        reposted=bool(raw.get("repostedJob")),
        scraped_at=captured,
        extractor_version=EXTRACTOR_VERSION,
        company={},
        provenance=dict(provenance or {}),
        signals={},
    )


def _text(value: Any) -> str | None:
    if value is None:
        return None
    result = " ".join(str(value).split())
    return result or None


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for value_item in value if (item := _text(value_item))]
    return [item for part in str(value).split(",") if (item := _text(part))]


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except Exception:
        return None


def _integer(value: Any) -> int | None:
    if value is None:
        return None
    digits = "".join(char for char in str(value) if char.isdigit())
    return int(digits) if digits else None


def _workplace(value: Any) -> str:
    text = (_text(value) or "").upper().replace("-", "_").replace(" ", "_")
    if "REMOTE" in text:
        return "REMOTE"
    if "HYBRID" in text:
        return "HYBRID"
    if "ON_SITE" in text or "ONSITE" in text:
        return "ON_SITE"
    return "UNKNOWN"


def _state(value: Any) -> str:
    return {"LISTED": "ACTIVE", "ACTIVE": "ACTIVE", "CLOSED": "CLOSED", "EXPIRED": "EXPIRED"}.get(
        str(value or "").upper(), "DISCOVERED"
    )
