"""Tests for Module 5: Feasibility Filter Engine and Module 6: Optimizer."""
from tests.utils import assert_json_error


def test_feasibility_filter_default(client):
    resp = client.post("/feasibility/filter", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_candidates"] == 15
    assert body["viable_candidates_count"] == 15
    assert len(body["viable_interventions"]) == 15
    assert len(body["filter_matrix"]) == 15
    for row in body["filter_matrix"]:
        assert row["passed_all"] is True


def test_feasibility_filter_budget_cap_rejects(client):
    resp = client.post("/feasibility/filter", json={"budget_limit_inr": 5000000})
    assert resp.status_code == 200
    body = resp.json()
    # Only INT-013 (₹4.0M) fits under a ₹5.0M cap
    assert body["viable_candidates_count"] >= 1
    assert body["viable_candidates_count"] < body["total_candidates"]
    for row in body["filter_matrix"]:
        if not row["passed_all"]:
            assert row["failure_reasons"]


def test_feasibility_filter_candidate_ids(client):
    resp = client.post(
        "/feasibility/filter",
        json={"candidate_intervention_ids": ["INT-001", "INT-002", "INT-003"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_candidates"] == 3


def test_feasibility_filter_time_horizon(client):
    # A 4-month horizon rejects the 6-month INT-001 but keeps 4-month INT-010
    resp = client.post("/feasibility/filter", json={"time_horizon_months": 4})
    assert resp.status_code == 200
    body = resp.json()
    assert body["viable_candidates_count"] < 15


def test_optimize_run(client):
    payload = {
        "geography_id": "rewa",
        "budget_limit_inr": 200000000.0,
        "time_horizon_months": 36,
    }
    resp = client.post("/optimize/run", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["budget_inr"] == 200000000.0
    assert body["pareto_solutions_count"] >= 1
    assert body["portfolios"]
    first = body["portfolios"][0]
    assert first["id"]
    assert first["total_cost_inr"] <= 200000000.0
    assert first["interventions"]


def test_optimize_run_v1_prefix(client):
    resp = client.post(
        "/api/v1/optimize/run",
        json={"budget_limit_inr": 100000000.0, "time_horizon_months": 36},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
