from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_compile_search_endpoint() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/searches/compile",
        json={
            "titles": ["Python Developer"],
            "locations": ["Prague", "Remote"],
            "posted_within_days": 3,
            "exclude_keywords": ["intern"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "Python Developer" in payload["search_text"]
    assert payload["deterministic_filters"]["locations"] == ["Prague", "Remote"]
