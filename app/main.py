import base64
import hashlib
import hmac
import json
import os
import time
from uuid import uuid4

import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine
from app.models import Customer, Integration, Tenant
from app.schemas import (
    CustomerCreate,
    CustomerOut,
    CustomerUpdate,
    IntegrationCreate,
    IntegrationOut,
    IntegrationTestResult,
    TenantCreate,
    TenantOut,
    TenantUpdate,
)

app = FastAPI(title="RTK CRM API", version="0.7.0")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
Base.metadata.create_all(bind=engine)


class LoginPayload(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthMeResponse(BaseModel):
    username: str


def _token_secret() -> str:
    return os.getenv("JWT_SECRET") or os.getenv("RTK_AUTH_SECRET", "change-me-in-production")


def _token_ttl_seconds() -> int:
    return int(os.getenv("RTK_AUTH_TTL_SECONDS", "43200"))


def _kms_key() -> bytes:
    raw = os.getenv("INTEGRATIONS_KMS_KEY")
    if not raw:
        raise HTTPException(status_code=500, detail="INTEGRATIONS_KMS_KEY not configured")
    try:
        key = base64.b64decode(raw)
    except Exception:
        key = raw.encode()
    if len(key) != 32:
        raise HTTPException(status_code=500, detail="INTEGRATIONS_KMS_KEY must be 32 bytes (base64)")
    return key


def _encrypt_config(config: dict) -> str:
    aesgcm = AESGCM(_kms_key())
    nonce = os.urandom(12)
    plaintext = json.dumps(config, separators=(",", ":"), sort_keys=True).encode()
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return base64.b64encode(nonce + ciphertext).decode()


def _decrypt_config(value: str) -> dict:
    raw = base64.b64decode(value)
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(_kms_key())
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext.decode())


def _sign_token(payload: dict) -> str:
    body_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    body = base64.urlsafe_b64encode(body_json.encode()).decode().rstrip("=")
    signature = hmac.new(_token_secret().encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def _decode_token(token: str) -> dict:
    try:
        body, signature = token.split(".", 1)
    except ValueError as error:
        raise HTTPException(status_code=401, detail="Invalid token") from error

    expected_signature = hmac.new(_token_secret().encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid token signature")

    padded = body + "=" * (-len(body) % 4)
    payload_raw = base64.urlsafe_b64decode(padded.encode()).decode()
    payload = json.loads(payload_raw)

    if payload.get("exp", 0) < int(time.time()):
        raise HTTPException(status_code=401, detail="Token expired")

    return payload


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization.split(" ", 1)[1].strip()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_tenant_id(x_tenant_id: str | None = Header(default=None)) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header required")
    return x_tenant_id


def _get_tenant_integration(db: Session, tenant_id: str, provider: str) -> Integration:
    row = db.query(Integration).filter(Integration.tenant_id == tenant_id, Integration.provider == provider).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"{provider} integration not configured")
    return row


def _uisp_headers(config: dict) -> dict:
    headers = {"accept": "application/json"}
    if config.get("token"):
        headers["Authorization"] = f"Bearer {config['token']}"
    if config.get("app_key"):
        headers["X-App-Key"] = config["app_key"]
    if config.get("api_key") and "Authorization" not in headers:
        headers["Authorization"] = f"Bearer {config['api_key']}"
    return headers


def _normalize_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


@app.get("/", response_class=HTMLResponse)
def web_app(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login", response_model=LoginResponse)
def auth_login(payload: LoginPayload) -> LoginResponse:
    admin_user = os.getenv("RTK_ADMIN_USER", "admin")
    admin_password = os.getenv("RTK_ADMIN_PASSWORD", "admin123")
    if payload.username != admin_user or payload.password != admin_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token_payload = {"sub": payload.username, "role": "admin", "exp": int(time.time()) + _token_ttl_seconds()}
    return LoginResponse(access_token=_sign_token(token_payload))


@app.get("/auth/me", response_model=AuthMeResponse)
def auth_me(authorization: str | None = Header(default=None)) -> AuthMeResponse:
    token = _extract_bearer_token(authorization)
    payload = _decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return AuthMeResponse(username=username)


@app.post("/tenants", response_model=TenantOut)
def create_tenant(payload: TenantCreate, tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> Tenant:
    tenant = Tenant(id=str(uuid4()), name=payload.name, network_name=payload.network_name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@app.get("/tenants", response_model=list[TenantOut])
def list_tenants(tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> list[Tenant]:
    return db.query(Tenant).order_by(Tenant.name.asc()).all()


@app.get("/tenants/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: str, x_tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@app.put("/tenants/{tenant_id}", response_model=TenantOut)
def update_tenant(tenant_id: str, payload: TenantUpdate, x_tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant.name = payload.name
    tenant.network_name = payload.network_name
    db.commit()
    db.refresh(tenant)
    return tenant


@app.delete("/tenants/{tenant_id}")
def delete_tenant(tenant_id: str, x_tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> dict[str, str]:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    db.delete(tenant)
    db.commit()
    return {"status": "deleted"}


@app.post("/customers", response_model=CustomerOut)
def create_customer(payload: CustomerCreate, tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> Customer:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    customer = Customer(id=str(uuid4()), tenant_id=tenant_id, name=payload.name, email=payload.email, plan_name=payload.plan_name, status=payload.status)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@app.get("/customers", response_model=list[CustomerOut])
def list_customers(tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> list[Customer]:
    return db.query(Customer).filter(Customer.tenant_id == tenant_id).order_by(Customer.name.asc()).all()


@app.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: str, tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> Customer:
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.tenant_id == tenant_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.put("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: str, payload: CustomerUpdate, tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> Customer:
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.tenant_id == tenant_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer.name = payload.name
    customer.email = payload.email
    customer.plan_name = payload.plan_name
    customer.status = payload.status
    db.commit()
    db.refresh(customer)
    return customer


@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: str, tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> dict[str, str]:
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.tenant_id == tenant_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(customer)
    db.commit()
    return {"status": "deleted"}


@app.post("/integrations", response_model=IntegrationOut)
def upsert_integration(payload: IntegrationCreate, tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> IntegrationOut:
    provider = payload.provider.lower()
    if provider not in {"uisp", "chatwoot", "n8n"}:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    row = db.query(Integration).filter(Integration.tenant_id == tenant_id, Integration.provider == provider).first()
    encrypted = _encrypt_config(payload.config)

    if row:
        row.config_encrypted = encrypted
    else:
        row = Integration(id=str(uuid4()), tenant_id=tenant_id, provider=provider, config_encrypted=encrypted)
        db.add(row)

    db.commit()
    db.refresh(row)
    return IntegrationOut(id=row.id, tenant_id=row.tenant_id, provider=row.provider, config_keys=sorted(list(payload.config.keys())))


@app.get("/integrations", response_model=list[IntegrationOut])
def list_integrations(tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> list[IntegrationOut]:
    rows = db.query(Integration).filter(Integration.tenant_id == tenant_id).order_by(Integration.provider.asc()).all()
    result: list[IntegrationOut] = []
    for row in rows:
        config = _decrypt_config(row.config_encrypted)
        result.append(IntegrationOut(id=row.id, tenant_id=row.tenant_id, provider=row.provider, config_keys=sorted(list(config.keys()))))
    return result


@app.post("/integrations/{integration_id}/connection-test", response_model=IntegrationTestResult)
def test_integration_connection(integration_id: str, tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> IntegrationTestResult:
    row = db.query(Integration).filter(Integration.id == integration_id, Integration.tenant_id == tenant_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")

    config = _decrypt_config(row.config_encrypted)
    target_url = config.get("base_url") or config.get("url")
    if not target_url:
        raise HTTPException(status_code=400, detail="Integration config must include base_url or url")

    headers = {}
    if config.get("api_key"):
        headers["Authorization"] = f"Bearer {config['api_key']}"

    try:
        response = httpx.get(target_url, timeout=5.0, headers=headers)
        ok = response.status_code < 400
        return IntegrationTestResult(ok=ok, status_code=response.status_code, detail="ok" if ok else "connection failed")
    except Exception as error:
        return IntegrationTestResult(ok=False, status_code=None, detail=str(error))


@app.post("/integrations/uisp/test", response_model=IntegrationTestResult)
def test_uisp(tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> IntegrationTestResult:
    row = _get_tenant_integration(db, tenant_id, "uisp")
    config = _decrypt_config(row.config_encrypted)
    base_url = config.get("base_url")
    if not base_url:
        raise HTTPException(status_code=400, detail="UISP base_url missing")

    try:
        response = httpx.get(_normalize_url(base_url, "/nms/api/v2.1/sites"), params={"limit": 1}, headers=_uisp_headers(config), timeout=6.0)
        ok = response.status_code < 400
        return IntegrationTestResult(ok=ok, status_code=response.status_code, detail="ok" if ok else "uisp connection failed")
    except Exception as error:
        return IntegrationTestResult(ok=False, status_code=None, detail=str(error))


@app.get("/integrations/uisp/search")
def uisp_search(query: str = Query(min_length=1), tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> dict:
    row = _get_tenant_integration(db, tenant_id, "uisp")
    config = _decrypt_config(row.config_encrypted)
    base_url = config.get("base_url")
    if not base_url:
        raise HTTPException(status_code=400, detail="UISP base_url missing")

    urls = [
        _normalize_url(base_url, "/crm/api/v1.0/clients"),
        _normalize_url(base_url, "/nms/api/v2.1/clients"),
    ]

    last_error = None
    for url in urls:
        try:
            response = httpx.get(url, params={"query": query, "limit": 25}, headers=_uisp_headers(config), timeout=8.0)
            if response.status_code >= 400:
                last_error = f"{url} -> {response.status_code}"
                continue
            data = response.json()
            if isinstance(data, dict):
                items = data.get("items", data.get("results", []))
            else:
                items = data
            normalized = []
            for item in items:
                normalized.append(
                    {
                        "id": item.get("id") or item.get("clientId") or item.get("uuid"),
                        "name": item.get("name") or item.get("fullName") or "(sin nombre)",
                        "email": item.get("email") or item.get("contactEmail"),
                        "status": item.get("status") or "unknown",
                    }
                )
            return {"results": normalized}
        except Exception as error:
            last_error = str(error)

    raise HTTPException(status_code=502, detail=f"UISP search failed: {last_error}")


@app.get("/integrations/uisp/customer/{customer_id}/services")
def uisp_customer_services(customer_id: str, tenant_id: str = Depends(require_tenant_id), db: Session = Depends(get_db)) -> dict:
    row = _get_tenant_integration(db, tenant_id, "uisp")
    config = _decrypt_config(row.config_encrypted)
    base_url = config.get("base_url")
    if not base_url:
        raise HTTPException(status_code=400, detail="UISP base_url missing")

    urls = [
        _normalize_url(base_url, f"/crm/api/v1.0/clients/{customer_id}/services"),
        _normalize_url(base_url, f"/nms/api/v2.1/clients/{customer_id}/services"),
    ]

    last_error = None
    for url in urls:
        try:
            response = httpx.get(url, headers=_uisp_headers(config), timeout=8.0)
            if response.status_code >= 400:
                last_error = f"{url} -> {response.status_code}"
                continue
            data = response.json()
            if isinstance(data, dict):
                items = data.get("items", data.get("results", []))
            else:
                items = data
            return {"customer_id": customer_id, "services": items}
        except Exception as error:
            last_error = str(error)

    raise HTTPException(status_code=502, detail=f"UISP services failed: {last_error}")
