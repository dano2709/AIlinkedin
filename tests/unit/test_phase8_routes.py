from apps.api.app.main_phase8 import app


def test_scoring_routes_are_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/jobs/{job_id}/score" in paths
    assert "post" in paths["/api/v1/jobs/{job_id}/score"]
    assert "get" in paths["/api/v1/jobs/{job_id}/score"]
