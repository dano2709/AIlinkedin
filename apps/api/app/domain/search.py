from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


LINKEDIN_JOBS_HOSTS = {"www.linkedin.com", "linkedin.com"}


@dataclass(slots=True)
class SearchQuery:
    titles: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    remote: bool | None = None
    workplace_types: list[str] = field(default_factory=list)
    employment_types: list[str] = field(default_factory=list)
    seniority: list[str] = field(default_factory=list)
    companies: list[str] = field(default_factory=list)
    posted_within_days: int | None = None
    exclude_keywords: list[str] = field(default_factory=list)
    easy_apply: bool | None = None
    under10_applicants: bool | None = None
    natural_language_query: str | None = None
    source_url: str | None = None


@dataclass(slots=True)
class PostFilters:
    titles: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    remote: bool | None = None
    workplace_types: list[str] = field(default_factory=list)
    employment_types: list[str] = field(default_factory=list)
    seniority: list[str] = field(default_factory=list)
    companies: list[str] = field(default_factory=list)
    posted_within_days: int | None = None
    exclude_keywords: list[str] = field(default_factory=list)
    easy_apply: bool | None = None
    under10_applicants: bool | None = None


@dataclass(slots=True)
class CompiledSearch:
    search_text: str
    linkedin_url: str | None
    structured_constraints: dict
    deterministic_filters: PostFilters
    ai_constraints: dict
    unsupported_constraints: list[str]


class SearchQueryCompiler:
    def compile(self, query: SearchQuery) -> CompiledSearch:
        source_url = self._normalize_source_url(query.source_url)
        search_text = self._build_search_text(query)

        deterministic = PostFilters(
            titles=list(query.titles),
            locations=list(query.locations),
            remote=query.remote,
            workplace_types=list(query.workplace_types),
            employment_types=list(query.employment_types),
            seniority=list(query.seniority),
            companies=list(query.companies),
            posted_within_days=query.posted_within_days,
            exclude_keywords=list(query.exclude_keywords),
            easy_apply=query.easy_apply,
            under10_applicants=query.under10_applicants,
        )

        unsupported: list[str] = []
        if query.source_url and not source_url:
            unsupported.append("source_url")

        return CompiledSearch(
            search_text=search_text,
            linkedin_url=source_url or self._build_basic_linkedin_url(search_text, query.locations),
            structured_constraints={
                "titles": query.titles,
                "keywords": query.keywords,
                "locations": query.locations,
                "remote": query.remote,
                "workplace_types": query.workplace_types,
                "employment_types": query.employment_types,
                "seniority": query.seniority,
                "companies": query.companies,
                "posted_within_days": query.posted_within_days,
                "exclude_keywords": query.exclude_keywords,
                "easy_apply": query.easy_apply,
                "under10_applicants": query.under10_applicants,
            },
            deterministic_filters=deterministic,
            ai_constraints={},
            unsupported_constraints=unsupported,
        )

    def _build_search_text(self, query: SearchQuery) -> str:
        parts: list[str] = []
        if query.natural_language_query:
            parts.append(query.natural_language_query.strip())
        if query.titles:
            parts.append(" OR ".join(t.strip() for t in query.titles if t.strip()))
        if query.keywords:
            parts.extend(k.strip() for k in query.keywords if k.strip())
        return " ".join(parts).strip()

    def _normalize_source_url(self, source_url: str | None) -> str | None:
        if not source_url:
            return None
        parsed = urlparse(source_url.strip())
        if parsed.scheme != "https" or parsed.netloc.lower() not in LINKEDIN_JOBS_HOSTS:
            return None
        if not parsed.path.startswith("/jobs/"):
            return None
        query = parse_qs(parsed.query, keep_blank_values=False)
        clean_query = urlencode(query, doseq=True)
        return urlunparse(("https", "www.linkedin.com", parsed.path, "", clean_query, ""))

    def _build_basic_linkedin_url(self, search_text: str, locations: list[str]) -> str:
        if not search_text and not locations:
            return "https://www.linkedin.com/jobs/"
        params: list[tuple[str, str]] = []
        if search_text:
            params.append(("keywords", search_text))
        if locations:
            params.append(("location", locations[0]))
        return f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"
