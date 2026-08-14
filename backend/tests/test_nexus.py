"""Tests for the Master Orchestration pipeline (``/nexus``).

Also includes an import smoke test that enumerates every registered route
and verifies these routes actually exist in the running app.
"""
import time


def test_all_endpoints_registered(app):
    """Sanity-check that every documented route is mounted.

    FastAPI >= 0.120 wraps included routers in ``_IncludedRouter`` objects that
    do not expose ``.path`` directly, so we enumerate from the generated
    OpenAPI schema instead.
    """
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    expected = {
        "/",
        "/health", "/ready", "/api/v1/system/status",
        "/auth/register", "/auth/login", "/auth/me", "/auth/onboarding",
        "/workspace/current",
        "/eo/layers",
        "/water/analyze", "/api/v1/water/analyze",
        "/context/{geography_id}/signals",
        "/graph/interventions", "/graph/chains/{intervention_id}", "/graph/discover",
        "/feasibility/filter",
        "/optimize/run", "/api/v1/optimize/run",
        "/portfolio/pareto", "/portfolio/{portfolio_id}/implementation-plan",
        "/provenance/{portfolio_id}",
        "/interventions/",
        "/map/metadata", "/map/overlay/{layer_type}",
        "/nexus/analyze", "/api/v1/nexus/analyze",
        "/nexus/jobs/{job_id}", "/api/v1/nexus/jobs/{job_id}",
        "/api/v1/maps/health", "/api/v1/maps", "/api/v1/maps/{record_id}",
        "/api/v1/maps/{record_id}/geojson",
        "/api/v1/budget", "/api/v1/locations", "/api/v1/locations/{record_id}",
        "/api/v1/timeline",
        "/api/v1/social/taxonomy", "/api/v1/social/groups",
        "/api/v1/social/groups/{record_id}",
    }
    missing = expected - paths
    assert not missing, f"Missing routes: {missing}"


def test_nexus_analyze_and_poll(client):
    resp = client.post("/api/v1/nexus/analyze", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"].startswith("job-")
    assert body["status"] == "PROCESSING"
    # The worker thread may advance progress between submit and our read.
    assert 0 <= body["progress_percent"] <= 100

    job_id = body["job_id"]

    # Poll until the background worker completes (with an upper bound).
    final = None
    for _ in range(200):
        status = client.get(f"/api/v1/nexus/jobs/{job_id}").json()
        if status["status"] in ("COMPLETED", "FAILED"):
            final = status
            break
        time.sleep(0.05)

    assert final is not None, "job never reached a terminal state"
    assert final["status"] == "COMPLETED", final.get("error_message")
    assert final["progress_percent"] == 100
    assert final["result"] is not None
    result = final["result"]
    assert result["geography_id"] == "rewa"
    assert result["earth_observation"]
    assert result["water_intelligence"]
    assert result["intervention_graph"]
    assert result["feasibility"]
    assert result["optimization"]
    assert result["implementation_plan"] is not None


def test_nexus_analyze_unprefixed(client):
    resp = client.post("/nexus/analyze", json={})
    assert resp.status_code == 200
    assert resp.json()["job_id"].startswith("job-")


def test_nexus_job_not_found(client):
    resp = client.get("/api/v1/nexus/jobs/job-does-not-exist")
    assert resp.status_code == 404


def test_nexus_analyze_invalid_bbox(client):
    payload = {"bbox": [82.0, 24.4, 81.5, 24.8]}
    resp = client.post("/api/v1/nexus/analyze", json=payload)
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"] == "AOI_LIMIT_EXCEEDED"
