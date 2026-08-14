"""Tests for root, health, readiness, and system status endpoints."""
from tests.utils import assert_json_error


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "online"
    assert body["version"] == "2.0.0"
    assert body["documentation"] == "/docs"
    assert body["master_pipeline_endpoint"] == "/api/v1/nexus/analyze"


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "uptime_seconds" in body


def test_readiness_endpoint(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert "database" in body
    assert "redis" in body


def test_system_status_endpoint(client):
    resp = client.get("/api/v1/system/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["application_version"] == "2.0.0"
    for field in (
        "api_status",
        "database_status",
        "eo_provider_status",
        "intelligence_engine_status",
        "optimizer_status",
        "background_worker_status",
        "timestamp",
    ):
        assert field in body


def test_unknown_route_returns_404(client):
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404


def test_docs_available(client):
    docs = client.get("/docs")
    assert docs.status_code == 200
    redoc = client.get("/redoc")
    assert redoc.status_code == 200
