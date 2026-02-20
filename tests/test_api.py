import os

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_web_home_available() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "RTK CRM" in response.text


def test_auth_login_and_me() -> None:
    os.environ["RTK_ADMIN_USER"] = "admin"
    os.environ["RTK_ADMIN_PASSWORD"] = "pass123"

    wrong = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert wrong.status_code == 401

    login = client.post("/auth/login", json={"username": "admin", "password": "pass123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "admin"

    os.environ.pop("RTK_ADMIN_USER", None)
    os.environ.pop("RTK_ADMIN_PASSWORD", None)


def test_company_hierarchy_and_listing() -> None:
    parent = client.post(
        "/companies",
        json={"name": "ISP Matriz", "network_name": "core-network"},
    )
    assert parent.status_code == 200
    parent_id = parent.json()["id"]

    child = client.post(
        "/companies",
        json={
            "name": "ISP Revendedor", "network_name": "reseller-segment", "parent_company_id": parent_id
        },
    )
    assert child.status_code == 200

    companies = client.get("/companies")
    assert companies.status_code == 200
    assert len(companies.json()) >= 2


def test_customer_suspend_syncs_uisp_and_triggers_n8n_automation() -> None:
    company = client.post(
        "/companies",
        json={"name": "ISP Uno", "network_name": "segment-a"},
    ).json()
    company_id = company["id"]

    automation = client.post(
        f"/companies/{company_id}/automations",
        json={
            "name": "Suspension Flow",
            "event": "customer.status_changed",
            "enabled": True,
            "target_webhook": "https://n8n.example.com/webhook/suspend",
        },
    )
    assert automation.status_code == 200

    customer = client.post(
        f"/companies/{company_id}/customers",
        json={
            "name": "Cliente Demo",
            "email": "cliente@example.com",
            "plan_name": "100Mbps",
        },
    ).json()

    response = client.post(
        f"/companies/{company_id}/customers/{customer['id']}/status",
        json={"status": "suspended", "reason": "Mora"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["customer"]["status"] == "suspended"
    assert data["uisp"]["synced"] is True
    assert len(data["automations"]) == 1
    assert data["automations"][0]["provider"] == "n8n"


def test_dashboard_counts() -> None:
    company = client.post(
        "/companies",
        json={"name": "ISP Dos", "network_name": "segment-b"},
    ).json()
    company_id = company["id"]

    integration = client.post(
        f"/companies/{company_id}/integrations",
        json={"type": "openai", "config": {"api_key": "sk-***", "model": "gpt-4o-mini"}},
    )
    assert integration.status_code == 200

    customer = client.post(
        f"/companies/{company_id}/customers",
        json={
            "name": "Cliente Activo",
            "email": "activo@example.com",
            "plan_name": "50Mbps",
        },
    ).json()

    suspend = client.post(
        f"/companies/{company_id}/customers/{customer['id']}/status",
        json={"status": "suspended", "reason": "Solicitud"},
    )
    assert suspend.status_code == 200

    dashboard = client.get(f"/companies/{company_id}/dashboard")
    assert dashboard.status_code == 200
    info = dashboard.json()
    assert info["total_customers"] == 1
    assert info["suspended_customers"] == 1
    assert "openai" in info["integrations"]


def test_api_key_protection() -> None:
    os.environ["RTK_API_KEY"] = "secret"
    unauthorized = client.get("/companies")
    assert unauthorized.status_code == 401

    authorized = client.get("/companies", headers={"x-api-key": "secret"})
    assert authorized.status_code == 200

    os.environ.pop("RTK_API_KEY", None)
