from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import hashlib
import json
from typing import Any

from ..domain.detail import CanonicalRecord


def _stable(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (list, tuple)):
        return json.dumps(list(value), ensure_ascii=False, sort_keys=True, default=str)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value or "")


def content_hash(value: Any) -> str:
    return hashlib.sha256(_stable(value).encode("utf-8")).hexdigest()


def snapshot_payload(job: CanonicalRecord) -> dict[str, object]:
    return {
        "title": job.title,
        "description": job.description,
        "responsibilities": job.responsibilities,
        "requirements": job.requirements,
        "preferred_qualifications": job.preferred_qualifications,
        "benefits": job.benefits,
        "skills": job.skills,
        "technologies": job.technologies,
        "salary_raw": job.salary_raw,
        "salary_min": str(job.salary_min) if job.salary_min is not None else None,
        "salary_max": str(job.salary_max) if job.salary_max is not None else None,
        "salary_currency": job.salary_currency,
        "salary_period": job.salary_period,
        "location_raw": job.location_raw,
        "city": job.city,
        "region": job.region,
        "country": job.country,
        "country_code": job.country_code,
        "apply_type": job.apply_type,
        "apply_url": job.apply_url,
        "external_apply_url": job.external_apply_url,
        "ats_provider": job.ats_provider,
        "applicant_count": job.applicant_count,
        "state": job.state,
        "reposted": job.reposted,
        "signals": job.signals,
    }


def snapshot_hashes(job: CanonicalRecord) -> dict[str, str]:
    return {
        "description_hash": content_hash(job.description),
        "requirements_hash": content_hash(job.requirements),
        "salary_hash": content_hash(
            [job.salary_raw, job.salary_min, job.salary_max, job.salary_currency, job.salary_period]
        ),
        "location_hash": content_hash(
            [job.location_raw, job.city, job.region, job.country_code, job.workplace_type]
        ),
        "apply_url_hash": content_hash([job.apply_url, job.external_apply_url]),
    }


def dedupe_fingerprint(job: CanonicalRecord, company_name: str | None = None) -> str:
    values = [
        job.normalized_title,
        (company_name or "").casefold().strip(),
        (job.city or "").casefold().strip(),
        (job.country_code or "").casefold().strip(),
    ]
    return content_hash(values)[:40]
