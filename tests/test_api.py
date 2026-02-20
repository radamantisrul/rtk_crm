import os

from fastapi.testclient import TestClient

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


def test_tenant_crud() -> None:
    missing = client.post("/tenants", json={"name": "Tenant A", "network_name": "red-a"})
    assert missing.status_code == 400

    create = client.post("/tenants", headers={"X-Tenant-Id": "bootstrap"}, json={"name": "Tenant A", "network_name": "red-a"})
    assert create.status_code == 200
    tenant = create.json()

    listing = client.get("/tenants", headers={"X-Tenant-Id": "bootstrap"})
    assert listing.status_code == 200
    assert any(item["id"] == tenant["id"] for item in listing.json())

    update = client.put(f"/tenants/{tenant['id']}", headers={"X-Tenant-Id": "bootstrap"}, json={"name": "Tenant A1", "network_name": "red-a1"})
    assert update.status_code == 200
    assert update.json()["name"] == "Tenant A1"

    get_one = client.get(f"/tenants/{tenant['id']}", headers={"X-Tenant-Id": "bootstrap"})
    assert get_one.status_code == 200


def test_customers_require_tenant_header_and_crud() -> None:
    tenant = client.post("/tenants", headers={"X-Tenant-Id": "bootstrap"}, json={"name": "Tenant B", "network_name": "red-b"}).json()

    missing_header = client.get("/customers")
    assert missing_header.status_code == 400

    create = client.post(
        "/customers",
        headers={"X-Tenant-Id": tenant["id"]},
        json={"name": "Cliente Uno", "email": "uno@example.com", "plan_name": "100Mbps", "status": "active"},
    )
    assert create.status_code == 200
    customer = create.json()

    listing = client.get("/customers", headers={"X-Tenant-Id": tenant["id"]})
    assert listing.status_code == 200
    assert any(item["id"] == customer["id"] for item in listing.json())

    get_one = client.get(f"/customers/{customer['id']}", headers={"X-Tenant-Id": tenant["id"]})
    assert get_one.status_code == 200

    update = client.put(
        f"/customers/{customer['id']}",
        headers={"X-Tenant-Id": tenant["id"]},
        json={"name": "Cliente Uno 2", "email": "uno2@example.com", "plan_name": "200Mbps", "status": "suspended"},
    )
    assert update.status_code == 200
    assert update.json()["status"] == "suspended"

    delete = client.delete(f"/customers/{customer['id']}", headers={"X-Tenant-Id": tenant["id"]})
    assert delete.status_code == 200
