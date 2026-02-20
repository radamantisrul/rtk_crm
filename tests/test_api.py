import os

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_rtk.db")
os.environ.setdefault("INTEGRATIONS_KMS_KEY", "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=")

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200


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


def test_tenant_customer_and_integrations_flow() -> None:
    missing = client.post("/tenants", json={"name": "Tenant A", "network_name": "red-a"})
    assert missing.status_code == 400

    tenant = client.post(
        "/tenants",
        headers={"X-Tenant-Id": "bootstrap"},
        json={"name": "Tenant A", "network_name": "red-a"},
    ).json()

    customer = client.post(
        "/customers",
        headers={"X-Tenant-Id": tenant["id"]},
        json={"name": "Cliente Uno", "email": "uno@example.com", "plan_name": "100Mbps", "status": "active"},
    )
    assert customer.status_code == 200

    save_integration = client.post(
        "/integrations",
        headers={"X-Tenant-Id": tenant["id"]},
        json={"provider": "uisp", "config": {"base_url": "https://example.com", "api_key": "abc"}},
    )
    assert save_integration.status_code == 200

    integrations = client.get("/integrations", headers={"X-Tenant-Id": tenant["id"]})
    assert integrations.status_code == 200
    assert len(integrations.json()) == 1

    test_conn = client.post(
        f"/integrations/{integrations.json()[0]['id']}/test",
        headers={"X-Tenant-Id": tenant["id"]},
    )
    assert test_conn.status_code == 200
    assert "ok" in test_conn.json()
