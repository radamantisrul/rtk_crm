import os
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_rtk.db")
os.environ.setdefault("INTEGRATIONS_KMS_KEY", "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=")

from app.main import app

client = TestClient(app)


def _mock_response(status_code: int, payload):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = payload
    return response


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
        json={"provider": "uisp", "config": {"base_url": "https://example.com", "app_key": "app", "token": "tok"}},
    )
    assert save_integration.status_code == 200

    integrations = client.get("/integrations", headers={"X-Tenant-Id": tenant["id"]})
    assert integrations.status_code == 200
    assert len(integrations.json()) == 1


def test_uisp_endpoints() -> None:
    tenant = client.post(
        "/tenants",
        headers={"X-Tenant-Id": "bootstrap"},
        json={"name": "Tenant UISP", "network_name": "red-uisp"},
    ).json()

    client.post(
        "/integrations",
        headers={"X-Tenant-Id": tenant["id"]},
        json={"provider": "uisp", "config": {"base_url": "https://uisp.example", "app_key": "app", "token": "tok"}},
    )

    def fake_httpx_get(url, **kwargs):
        if "sites" in url:
            return _mock_response(200, [])
        if "services" in url:
            return _mock_response(200, [{"id": "svc1", "name": "Internet"}])
        return _mock_response(200, [{"id": "c1", "name": "Juan", "email": "juan@test.com", "status": "active"}])

    with patch("app.main.httpx.get", side_effect=fake_httpx_get):
        test_conn = client.post("/integrations/uisp/test", headers={"X-Tenant-Id": tenant["id"]})
        assert test_conn.status_code == 200
        assert test_conn.json()["ok"] is True

        search = client.get("/integrations/uisp/search", params={"query": "juan"}, headers={"X-Tenant-Id": tenant["id"]})
        assert search.status_code == 200
        assert len(search.json()["results"]) == 1

        services = client.get(f"/integrations/uisp/customer/c1/services", headers={"X-Tenant-Id": tenant["id"]})
        assert services.status_code == 200
        assert len(services.json()["services"]) == 1
