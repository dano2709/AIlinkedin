from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CandidateProfile, User


PROFILE_VERSION = 1


@dataclass(slots=True)
class CandidateProfileData:
    full_name: str | None
    headline: str | None
    summary: str | None
    target_titles: list[str]
    skills: list[str]
    technologies: list[str]
    certifications: list[str]
    education: list[str]
    languages: list[str]
    industries: list[str]
    preferred_locations: list[str]
    preferred_countries: list[str]
    workplace_types: list[str]
    employment_types: list[str]
    seniority: list[str]
    preferred_companies: list[str]
    excluded_companies: list[str]
    excluded_keywords: list[str]
    min_salary: str | None
    salary_currency: str | None
    years_experience: str | None
    willing_to_relocate: bool


@dataclass(slots=True)
class CandidateProfileResult:
    user_id: UUID
    profile_id: UUID | None
    data: CandidateProfileData
    exists: bool
    created_at: datetime | None
    updated_at: datetime | None


def normalize_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = " ".join(value.split())
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def normalize_profile(data: CandidateProfileData) -> CandidateProfileData:
    return CandidateProfileData(
        full_name=" ".join(data.full_name.split()) if data.full_name else None,
        headline=" ".join(data.headline.split()) if data.headline else None,
        summary=data.summary.strip() if data.summary else None,
        target_titles=normalize_list(data.target_titles),
        skills=normalize_list(data.skills),
        technologies=normalize_list(data.technologies),
        certifications=normalize_list(data.certifications),
        education=normalize_list(data.education),
        languages=normalize_list(data.languages),
        industries=normalize_list(data.industries),
        preferred_locations=normalize_list(data.preferred_locations),
        preferred_countries=normalize_list(data.preferred_countries),
        workplace_types=normalize_list(data.workplace_types),
        employment_types=normalize_list(data.employment_types),
        seniority=normalize_list(data.seniority),
        preferred_companies=normalize_list(data.preferred_companies),
        excluded_companies=normalize_list(data.excluded_companies),
        excluded_keywords=normalize_list(data.excluded_keywords),
        min_salary=data.min_salary.strip() if data.min_salary else None,
        salary_currency=data.salary_currency.upper().strip() if data.salary_currency else None,
        years_experience=data.years_experience.strip() if data.years_experience else None,
        willing_to_relocate=data.willing_to_relocate,
    )


class CandidateProfileService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, user_id: UUID) -> CandidateProfileResult:
        user = self.session.execute(
            select(User).where(User.id == user_id)
        ).scalars().first()
        if user is None:
            return CandidateProfileResult(
                user_id=user_id,
                profile_id=None,
                data=self._empty_data(),
                exists=False,
                created_at=None,
                updated_at=None,
            )

        return CandidateProfileResult(
            user_id=user.id,
            profile_id=profile.id,
            data=self._data_from_storage(profile.profile),
            exists=True,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def upsert(self, user_id: UUID, data: CandidateProfileData) -> CandidateProfileResult:
        user = self._get_or_create_user(user_id)
        normalized = normalize_profile(data)
        payload = self._storage_from_data(normalized)

        profile = self.session.execute(
            select(CandidateProfile).where(CandidateProfile.user_id == user.id)
        ).scalars().first()

        if profile is None:
            profile = CandidateProfile(
                id=uuid4(),
                user_id=user.id,
                profile=payload,
            )
            self.session.add(profile)
        else:
            profile.profile = payload

        self.session.flush()

        return CandidateProfileResult(
            user_id=user.id,
            profile_id=profile.id,
            data=normalized,
            exists=True,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    @staticmethod
    def _empty_data() -> CandidateProfileData:
        return CandidateProfileData(
            full_name=None,
            headline=None,
            summary=None,
            target_titles=[],
            skills=[],
            technologies=[],
            certifications=[],
            education=[],
            languages=[],
            industries=[],
            preferred_locations=[],
            preferred_countries=[],
            workplace_types=[],
            employment_types=[],
            seniority=[],
            preferred_companies=[],
            excluded_companies=[],
            excluded_keywords=[],
            min_salary=None,
            salary_currency=None,
            years_experience=None,
            willing_to_relocate=False,
        )

    @staticmethod
    def _storage_from_data(data: CandidateProfileData) -> dict[str, object]:
        return {
            "version": PROFILE_VERSION,
            "full_name": data.full_name,
            "headline": data.headline,
            "summary": data.summary,
            "target_titles": data.target_titles,
            "skills": data.skills,
            "technologies": data.technologies,
            "certifications": data.certifications,
            "education": data.education,
            "languages": data.languages,
            "industries": data.industries,
            "preferred_locations": data.preferred_locations,
            "preferred_countries": data.preferred_countries,
            "workplace_types": data.workplace_types,
            "employment_types": data.employment_types,
            "seniority": data.seniority,
            "preferred_companies": data.preferred_companies,
            "excluded_companies": data.excluded_companies,
            "excluded_keywords": data.excluded_keywords,
            "min_salary": data.min_salary,
            "salary_currency": data.salary_currency,
            "years_experience": data.years_experience,
            "willing_to_relocate": data.willing_to_relocate,
        }

    def _get_user(self, user_id: UUID) -> User:
        user = self.session.execute(
            select(User).where(User.id == user_id)
        ).scalars().first()
        if user is None:
            user = User(id=user_id)
            self.session.add(user)
            self.session.flush()
        return user

    def _get_or_create_user(self, user_id: UUID) -> User:
        return self._get_user(user_id)

    @staticmethod
    def _data_from_storage(payload: dict[str, object]) -> CandidateProfileData:
        def text(key: str) -> str | None:
            value = payload.get(key)
            return str(value) if value not in (None, "") else None

        def list_value(key: str) -> list[str]:
            value = payload.get(key, [])
            if not isinstance(value, list):
                return []
            return [str(item) for item in value if item not in (None, "")]

        return CandidateProfileData(
            full_name=text("full_name"),
            headline=text("headline"),
            summary=text("summary"),
            target_titles=list_value("target_titles"),
            skills=list_value("skills"),
            technologies=list_value("technologies"),
            certifications=list_value("certifications"),
            education=list_value("education"),
            languages=list_value("languages"),
            industries=list_value("industries"),
            preferred_locations=list_value("preferred_locations"),
            preferred_countries=list_value("preferred_countries"),
            workplace_types=list_value("workplace_types"),
            employment_types=list_value("employment_types"),
            seniority=list_value("seniority"),
            preferred_companies=list_value("preferred_companies"),
            excluded_companies=list_value("excluded_companies"),
            excluded_keywords=list_value("excluded_keywords"),
            min_salary=text("min_salary"),
            salary_currency=text("salary_currency"),
            years_experience=text("years_experience"),
            willing_to_relocate=bool(payload.get("willing_to_relocate", False)),
        )
