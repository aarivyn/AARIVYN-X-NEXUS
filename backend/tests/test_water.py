"""Tests for Module 3: Water Intelligence Engine and Context signals."""
from tests.utils import assert_json_error


def test_water_analyze_default(client):
    resp = client.post("/water/analyze", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["geography_id"] == "rewa"
    # the offline MockEOProvider emits a single synthetic indicator
    assert len(body["water_indicators"]) >= 1
    assert len(body["detected_signals"]) == 3
    assert "water_stress" in body["problem_categories"]
    assert body["evidence_used"]
    assert body["confidence_metadata"]


def test_water_analyze_v1_prefix(client):
    resp = client.post("/api/v1/water/analyze", json={})
    assert resp.status_code == 200
    assert resp.json()["geography_id"] == "rewa"


def test_water_analyze_custom_payload(client):
    payload = {
        "geography_id": "rewa-test",
        "bbox": [81.1, 24.4, 81.2, 24.5],
        "date_range_start": "2026-03-01",
        "date_range_end": "2026-07-01",
        "data_sources": ["Sentinel-2"],
        "budget_inr": 100000000.0,
        "time_horizon_months": 24,
        "risk_tolerance": "LOW",
    }
    resp = client.post("/water/analyze", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["geography_id"] == "rewa-test"


def test_water_analyze_invalid_bbox(client):
    payload = {"bbox": [82.0, 24.4, 81.5, 24.8]}
    resp = client.post("/water/analyze", json=payload)
    body = assert_json_error(resp, 400)
    assert body["detail"]["error"] == "AOI_LIMIT_EXCEEDED"


def test_context_signals(client):
    resp = client.get("/context/rewa/signals")
    assert resp.status_code == 200
    body = resp.json()
    assert body["geography_id"] == "rewa"
    assert body["water_stress_index"] == 0.74
    assert body["vegetation_condition_index"] == 0.68
    assert body["flood_risk_score"] == 0.32
    assert body["groundwater_drawdown_rate_m_yr"] == -1.2
    assert len(body["signals"]) == 3
