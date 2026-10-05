from apps.api.app.domain.search import SearchQuery, SearchQueryCompiler


def test_compiler_keeps_constraints_for_post_filtering() -> None:
    compiled = SearchQueryCompiler().compile(
        SearchQuery(
            titles=["Python Developer"],
            keywords=["FastAPI"],
            locations=["Prague"],
            remote=True,
            posted_within_days=3,
            exclude_keywords=["intern"],
        )
    )

    assert "Python Developer" in compiled.search_text
    assert "FastAPI" in compiled.search_text
    assert compiled.deterministic_filters.remote is True
    assert compiled.deterministic_filters.posted_within_days == 3
    assert compiled.deterministic_filters.exclude_keywords == ["intern"]


def test_linkedin_source_url_is_normalized() -> None:
    compiled = SearchQueryCompiler().compile(
        SearchQuery(
            source_url="https://linkedin.com/jobs/search/?keywords=python&trk=guest_homepage-basic_jobs_search"
        )
    )

    assert compiled.linkedin_url is not None
    assert compiled.linkedin_url.startswith("https://www.linkedin.com/jobs/search/?")
    assert "keywords=python" in compiled.linkedin_url


def test_invalid_source_url_is_rejected_but_pipeline_has_a_safe_fallback() -> None:
    compiled = SearchQueryCompiler().compile(
        SearchQuery(source_url="https://example.com/jobs/search/?keywords=python")
    )

    assert compiled.linkedin_url == "https://www.linkedin.com/jobs/"
    assert "source_url" in compiled.unsupported_constraints


def test_empty_query_defaults_to_linkedin_jobs_home() -> None:
    compiled = SearchQueryCompiler().compile(SearchQuery())
    assert compiled.linkedin_url == "https://www.linkedin.com/jobs/"
