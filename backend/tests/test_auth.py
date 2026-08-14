"""Tests for Module 1: Auth & Onboarding and Workspace Resolver."""
PERSONAS = [
    "GOVERNMENT", "CSR_FUNDER", "NGO", "STUDENT", "RESEARCHER", "COMMUNITY",
]


def test_register_user(client):
    resp = client.post(
        "/auth/register",
        json={"email": "officer@mp.gov.in", "password": "secret", "name": "Officer"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "registered"
    assert body["user_id"] == 1
    assert body["email"] == "officer@mp.gov.in"


def test_register_duplicate_rejected(client):
    client.post(
        "/auth/register",
        json={"email": "dup@mp.gov.in", "password": "secret", "name": "Dup"},
    )
    resp = client.post(
        "/auth/register",
        json={"email": "dup@mp.gov.in", "password": "secret", "name": "Dup"},
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_login_user(client):
    resp = client.post(
        "/auth/login",
        json={"email": "officer@mp.gov.in", "password": "secret"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "authenticated"
    assert body["access_token"].startswith("mock_bearer_token_for_")
    assert body["persona"] == "GOVERNMENT"


def test_get_current_user(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "officer@mp.gov.in"
    assert body["persona"] == "GOVERNMENT"


def test_onboarding_government(client):
    resp = client.post(
        "/auth/onboarding",
        json={
            "persona": "GOVERNMENT",
            "government": {
                "organization": "MPWRD",
                "department_agency": "Water Resources",
                "admin_level": "District",
                "role": "District Officer",
                "target_district": "Rewa",
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["persona"] == "GOVERNMENT"
    assert "Rewa" in body["geography_name"]


def test_onboarding_csr_funder(client):
    resp = client.post(
        "/auth/onboarding",
        json={
            "persona": "CSR_FUNDER",
            "csr_funder": {
                "organization": "Acme Corp",
                "funding_program": "Clean Water",
                "available_budget_inr": 50000000,
                "focus_areas": ["Water", "Sanitation"],
                "target_geography": "Rewa",
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["persona"] == "CSR_FUNDER"
    assert body["permission_scope"]["budget_cap_inr"] == 50000000


def test_workspace_current_default(client):
    resp = client.get("/workspace/current")
    assert resp.status_code == 200
    body = resp.json()
    assert body["persona"] == "GOVERNMENT"
    assert body["geography_name"] == "Rewa District, Madhya Pradesh"
    assert body["bbox"] == [81.1, 24.4, 81.5, 24.8]
    assert body["center"] == [24.6, 81.3]
    assert body["zoom"] == 10


def test_workspace_current_other_persona(client):
    resp = client.get("/workspace/current", params={"persona": "NGO"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["persona"] == "NGO"
    assert body["permission_scope"]["persona"] == "NGO"
