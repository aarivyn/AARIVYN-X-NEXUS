"""Tests for Module 7: Portfolios, Implementation Plans & Provenance."""
from tests.utils import assert_json_error


def test_pareto_portfolios(client):
    resp = client.get("/portfolio/pareto")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert len(body["portfolios"]) >= 1


def test_implementation_plan(client):
    resp = client.post("/portfolio/PORTFOLIO_1/implementation-plan")
    assert resp.status_code == 200
    body = resp.json()
    assert body["portfolio_id"] == "PORTFOLIO_1"
    assert body["total_cost_inr"] >= 0
    assert body["total_duration_months"] >= 12
    assert body["intervention_sequence"]
    assert body["monitoring_indicators"]
    assert body["created_at"]


def test_implementation_plan_unknown_id_falls_back(client):
    resp = client.post("/portfolio/DOES-NOT-EXIST/implementation-plan")
    assert resp.status_code == 200
    body = resp.json()
    # falls back to the first portfolio
    assert body["portfolio_id"]


def test_provenance_audit(client):
    resp = client.get("/provenance/PORTFOLIO_1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["portfolio_id"] == "PORTFOLIO_1"
    assert body["optimizer_engine"]
    assert body["objective_weights_applied"]["water_security_impact"] == "MAXIMIZE"
    assert body["objective_weights_applied"]["capital_and_operational_cost"] == "MINIMIZE"
    assert body["feasibility_filter_audit"]
    assert body["knowledge_graph_chain_sources"]
    assert body["earth_observation_scene_ids"]
    assert body["satellite_stac_provenance"]
    assert "HIGH" in body["confidence_score"]
