from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping

from .detail_utils import (
    as_bool,
    as_decimal,
    as_int,
    as_mapping,
    clean_list,
    clean_text,
    detect_ats,
    job_state,
    normalize_title,
    parse_posted_at,
    parse_salary_range,
    workplace_type,
)


EXTRACTOR_VERSION = "linkedin-bebity-v1"


@dataclass(slots=True)
class CanonicalCompany:
    source_company_id: str | None
    name: str | None
    url: str | None
    website: str | None
    logo_url: str | None
    employee_count: int | None
    industry: str | None
    industries: list[str] = field(default_factory=list)
    description: str | None = None
    tagline: str | None = None
    headquarters: dict[str, object] = field(default_factory=dict)
    employee_size: str | None = None
    follower_count: int | None = None
    company_type: str | None = None
    founded_year: int | None = None
    enrichment: dict[str, object] = field(default_factory=dict)


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
    responsibilities: list[str]
    requirements: list[str]
    preferred_qualifications: list[str]
    benefits: list[str]
    skills: list[str]
    technologies: list[str]
    certifications: list[str]
    education: list[str]
    languages: list[str]
    applicant_count: int | None
    apply_type: str | None
    apply_url: str | None
    external_apply_url: str | None
    ats_provider: str | None
    state: str
    reposted: bool
    scraped_at: datetime
    extractor_version: str
    company: CanonicalCompany | None
    provenance: dict[str, object]
    signals: dict[str, object]


class JobDetailExtractor:
    version = EXTRACTOR_VERSION

    def extract(
        self,
        raw: Mapping[str, Any],
        *,
        provenance: Mapping[str, Any] | None = None,
        captured_at: datetime | None = None,
    ) -> CanonicalRecord:
        captured = captured_at or datetime.now(timezone.utc)
        source_id = clean_text(raw.get("id"))
        if not source_id:
            raise ValueError("detail payload is missing id")

        title = clean_text(raw.get("title")) or "Untitled job"
        url = clean_text(raw.get("jobUrl")) or f"https://www.linkedin.com/jobs/view/{source_id}/"

        location = raw.get("locationParsed")
        city = region = country = country_code = None
        location_raw = clean_text(raw.get("location"))
        if isinstance(location, Mapping):
            city = clean_text(location.get("city"))
            region = clean_text(location.get("region"))
            country = clean_text(location.get("country"))
            if country and len(country) == 2:
                country_code = country.upper()
            location_raw = location_raw or clean_text(location.get("formatted"))

        salary_raw = clean_text(raw.get("salary"))
        salary_min = as_decimal(raw.get("salaryMin"))
        salary_max = as_decimal(raw.get("salaryMax"))
        if salary_min is None or salary_max is None:
            fallback_min, fallback_max = parse_salary_range(salary_raw)
            salary_min = salary_min or fallback_min
            salary_max = salary_max or fallback_max

        captured = captured.astimezone(timezone.utc) if captured.tzinfo else captured.replace(tzinfo=timezone.utc)
        posted_at, precision = parse_posted_at(
            raw.get("postedAtTimestamp"),
            raw.get("publishedAt"),
            raw.get("postedTime"),
            captured,
        )

        apply_type = clean_text(raw.get("applyType"))
        apply_url = clean_text(raw.get("applyUrl"))
        external_apply_url = apply_url if apply_type and apply_type.upper() in {"EXTERNAL", "EXTERNAL_APPLY"} else None

        combined_provenance: dict[str, object] = dict(provenance or {})
        if isinstance(raw.get("scrapingInfo"), Mapping):
            combined_provenance["scraping_info"] = dict(raw["scrapingInfo"])

        signals: dict[str, object] = {
            "verified": as_bool(raw.get("verified")),
            "reposted_job": as_bool(raw.get("repostedJob")),
            "job_state_raw": clean_text(raw.get("jobState")),
            "salary_source": clean_text(raw.get("salarySource")),
            "poster_full_name": clean_text(raw.get("posterFullName")),
            "poster_profile_url": clean_text(raw.get("posterProfileUrl")),
            "poster_headline": clean_text(raw.get("posterHeadline")),
            "poster_photo": clean_text(raw.get("posterPhoto")),
        }
        signals = {key: value for key, value in signals.items() if value not in (None, "", False)}

        return CanonicalRecord(
            source="linkedin",
            source_id=source_id,
            url=url,
            title=title,
            normalized_title=normalize_title(title),
            location_raw=location_raw,
            city=city,
            region=region,
            country=country,
            country_code=country_code,
            workplace_type=workplace_type(raw.get("workType")),
            remote_allowed=workplace_type(raw.get("workType")) == "REMOTE",
            posted_at=posted_at,
            posted_at_raw=clean_text(raw.get("publishedAt")) or clean_text(raw.get("postedTime")),
            posted_at_precision=precision,
            employment_type=clean_text(raw.get("contractType")),
            experience_level=clean_text(raw.get("experienceLevel")),
            job_function=clean_text(raw.get("jobFunction")),
            industry=clean_text(raw.get("sector")),
            salary_raw=salary_raw,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=(clean_text(raw.get("salaryCurrency")) or "").upper() or None,
            salary_period=(clean_text(raw.get("salaryPeriod")) or "").lower() or None,
            description=clean_text(raw.get("description")),
            responsibilities=clean_list(raw.get("responsibilities")),
            requirements=clean_list(raw.get("requirements")),
            preferred_qualifications=clean_list(raw.get("preferredQualifications")),
            benefits=clean_list(raw.get("benefits")),
            skills=clean_list(raw.get("skills")),
            technologies=clean_list(raw.get("technologies")),
            certifications=clean_list(raw.get("certifications")),
            education=clean_list(raw.get("education")),
            languages=clean_list(raw.get("languages")),
            applicant_count=as_int(raw.get("applicationsCount")),
            apply_type=apply_type,
            apply_url=apply_url,
            external_apply_url=external_apply_url,
            ats_provider=detect_ats(external_apply_url),
            state=job_state(raw.get("jobState")),
            reposted=as_bool(raw.get("repostedJob")),
            scraped_at=captured,
            extractor_version=self.version,
            company=self._company(raw),
            provenance=combined_provenance,
            signals=signals,
        )

    @staticmethod
    def _company(raw: Mapping[str, Any]) -> CanonicalCompany | None:
        name = clean_text(raw.get("companyName"))
        company_id = clean_text(raw.get("companyId"))
        company_url = clean_text(raw.get("companyUrl"))
        website = clean_text(raw.get("companyWebsite"))
        if not any((name, company_id, company_url, website)):
            return None

        industries = clean_list(raw.get("companyIndustries"))
        enrichment: dict[str, object] = {}
        for key in (
            "companyEmployeeCount",
            "companySize",
            "companyFollowerCount",
            "companyIndustries",
            "companyDescription",
            "companyTagline",
            "companyHeadquarters",
            "companyHeadquartersText",
            "companyType",
            "companyFoundedYear",
        ):
            value = raw.get(key)
            if value not in (None, ""):
                enrichment[key] = value

        return CanonicalCompany(
            source_company_id=company_id,
            name=name,
            url=company_url,
            website=website,
            logo_url=clean_text(raw.get("companyLogo")),
            employee_count=as_int(raw.get("companyEmployeeCount")),
            industry=industries[0] if industries else clean_text(raw.get("sector")),
            industries=industries,
            description=clean_text(raw.get("companyDescription")),
            tagline=clean_text(raw.get("companyTagline")),
            headquarters=as_mapping(raw.get("companyHeadquarters")),
            employee_size=clean_text(raw.get("companySize")),
            follower_count=as_int(raw.get("companyFollowerCount")),
            company_type=clean_text(raw.get("companyType")),
            founded_year=as_int(raw.get("companyFoundedYear")),
            enrichment=enrichment,
        )
