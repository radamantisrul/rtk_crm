import base64
import hashlib
import hmac
import json
import os
import time
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine
from app.models import Customer, Tenant
from app.schemas import CustomerCreate, CustomerOut, CustomerUpdate, TenantCreate, TenantOut, TenantUpdate

app = FastAPI(title="RTK CRM API", version="0.5.0")

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

    token_payload = {
        "sub": payload.username,
        "role": "admin",
        "exp": int(time.time()) + _token_ttl_seconds(),
    }
    return LoginResponse(access_token=_sign_token(token_payload))


@app.get("/auth/me", response_model=AuthMeResponse)
def auth_me(authorization: str | None = Header(default=None)) -> AuthMeResponse:
    token = _extract_bearer_token(authorization)
    payload = _decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return AuthMeResponse(username=username)


# Tenants CRUD
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


# Customers CRUD scoped by X-Tenant-Id
@app.post("/customers", response_model=CustomerOut)
def create_customer(
    payload: CustomerCreate,
    tenant_id: str = Depends(require_tenant_id),
    db: Session = Depends(get_db),
) -> Customer:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    customer = Customer(
        id=str(uuid4()),
        tenant_id=tenant_id,
        name=payload.name,
        email=payload.email,
        plan_name=payload.plan_name,
        status=payload.status,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@app.get("/customers", response_model=list[CustomerOut])
def list_customers(
    tenant_id: str = Depends(require_tenant_id),
    db: Session = Depends(get_db),
) -> list[Customer]:
    return db.query(Customer).filter(Customer.tenant_id == tenant_id).order_by(Customer.name.asc()).all()


@app.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: str,
    tenant_id: str = Depends(require_tenant_id),
    db: Session = Depends(get_db),
) -> Customer:
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.tenant_id == tenant_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.put("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: str,
    payload: CustomerUpdate,
    tenant_id: str = Depends(require_tenant_id),
    db: Session = Depends(get_db),
) -> Customer:
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
def delete_customer(
    customer_id: str,
    tenant_id: str = Depends(require_tenant_id),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.tenant_id == tenant_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(customer)
    db.commit()
    return {"status": "deleted"}
