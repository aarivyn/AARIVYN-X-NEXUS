"""Tests for Module 4: Intervention Knowledge Graph."""
from tests.utils import assert_json_error


def test_graph_interventions_all(client):
    resp = client.get("/graph/interventions")
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    # default domain=Water filters to the Water-flagged interventions
    assert len(items) >= 13
    # every card carries the expected shape
    for item in items:
        assert item["id"]
        assert item["name"]
        assert item["cost_inr"] >= 0


def test_graph_interventions_domain_filter(client):
    resp = client.get("/graph/interventions", params={"domain": "Agriculture"})
    assert resp.status_code == 200
    items = resp.json()
    assert items, "expected at least the bio-fertilizer intervention"
    assert all(i["domain"].lower() == "agriculture" for i in items)

def test_graph_interventions_unknown_domain_empty(client):
    resp = client.get("/graph/interventions", params={"domain": "Nope"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_graph_chain(client):
    resp = client.get("/graph/chains/INT-ALGAE-01")
    assert resp.status_code == 200
    body = resp.json()
    assert body["root_intervention_id"] == "INT-ALGAE-01"
    assert body["max_depth"] == 5
    assert body["path_nodes"], "expected path nodes"
    assert body["edges"], "expected edges"


def test_graph_chain_max_depth(client):
    resp = client.get("/graph/chains/PROB-WASTEWATER", params={"max_depth": 2})
    assert resp.status_code == 200
    assert resp.json()["max_depth"] == 2


def test_graph_discover(client):
    payload = {
        "detected_problem": "Untreated wastewater discharge",
        "geography_id": "rewa",
        "max_depth": 5,
    }
    resp = client.post("/graph/discover", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "discovered"
    assert body["reachable_interventions_count"] >= 1
    assert body["chain_graph"]
