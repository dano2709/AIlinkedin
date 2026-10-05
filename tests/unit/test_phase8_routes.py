from apps.api.app.main_phase8 import app


def test_scoring_routes_are_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/jobs/{job_id}/score" in paths
