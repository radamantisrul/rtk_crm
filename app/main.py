import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.schemas import (
    Automation,
    AutomationCreate,
    Company,
    CompanyCreate,
    Customer,
    CustomerCreate,
    CustomerStatusChange,
    Dashboard,
    Integration,
    IntegrationCreate,
)
from app.services import CRMService

app = FastAPI(title="RTK CRM API", version="0.4.0")
service = CRMService()

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


class LoginPayload(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthMeResponse(BaseModel):
    username: str


def _token_secret() -> str:
    return os.getenv("RTK_AUTH_SECRET", "change-me-in-production")


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


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected_api_key = os.getenv("RTK_API_KEY")
    if expected_api_key and x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


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


@app.post("/companies", response_model=Company, dependencies=[Depends(require_api_key)])
def create_company(payload: CompanyCreate) -> Company:
    try:
        return service.create_company(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/companies", response_model=list[Company], dependencies=[Depends(require_api_key)])
def list_companies() -> list[Company]:
    return service.list_companies()


@app.post("/companies/{company_id}/integrations", response_model=Integration, dependencies=[Depends(require_api_key)])
def create_integration(company_id: str, payload: IntegrationCreate) -> Integration:
    try:
        return service.create_integration(company_id, payload)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/companies/{company_id}/automations", response_model=Automation, dependencies=[Depends(require_api_key)])
def create_automation(company_id: str, payload: AutomationCreate) -> Automation:
    try:
        return service.create_automation(company_id, payload)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/companies/{company_id}/customers", response_model=Customer, dependencies=[Depends(require_api_key)])
def create_customer(company_id: str, payload: CustomerCreate) -> Customer:
    try:
        return service.create_customer(company_id, payload)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post(
    "/companies/{company_id}/customers/{customer_id}/status",
    dependencies=[Depends(require_api_key)],
)
def update_customer_status(company_id: str, customer_id: str, payload: CustomerStatusChange) -> dict:
    try:
        return service.change_customer_status(company_id, customer_id, payload)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/companies/{company_id}/dashboard", response_model=Dashboard, dependencies=[Depends(require_api_key)])
def get_dashboard(company_id: str) -> Dashboard:
    try:
        return service.get_dashboard(company_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
