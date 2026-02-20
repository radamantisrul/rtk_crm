import os
from fastapi import Depends, FastAPI, Header, HTTPException

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

app = FastAPI(title="RTK CRM API", version="0.3.0")
service = CRMService()


# Public endpoints (sin API key)
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "rtk_crm", "status": "ok"}


# API key dependency (protege endpoints de datos)
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("RTK_API_KEY", "")
    # Si no hay RTK_API_KEY configurada, no bloquea (modo dev)
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


# Protected endpoints
@app.post("/companies", response_model=Company, dependencies=[Depends(require_api_key)])
def create_company(payload: CompanyCreate) -> Company:
    try:
        return service.create_company(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/companies", response_model=list[Company], dependencies=[Depends(require_api_key)])
def list_companies() -> list[Company]:
    return service.list_companies()


@app.post(
    "/companies/{company_id}/integrations",
    response_model=Integration,
    dependencies=[Depends(require_api_key)],
)
def create_integration(company_id: str, payload: IntegrationCreate) -> Integration:
    try:
        return service.create_integration(company_id, payload)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post(
    "/companies/{company_id}/automations",
    response_model=Automation,
    dependencies=[Depends(require_api_key)],
)
def create_automation(company_id: str, payload: AutomationCreate) -> Automation:
    try:
        return service.create_automation(company_id, payload)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post(
    "/companies/{company_id}/customers",
    response_model=Customer,
    dependencies=[Depends(require_api_key)],
)
def create_customer(company_id: str, payload: CustomerCreate) -> Customer:
    try:
        return service.create_customer(company_id, payload)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post(
    "/companies/{company_id}/customers/{customer_id}/status",
    dependencies=[Depends(require_api_key)],
)
def update_customer_status(
    company_id: str, customer_id: str, payload: CustomerStatusChange
) -> dict:
    try:
        return service.change_customer_status(company_id, customer_id, payload)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get(
    "/companies/{company_id}/dashboard",
    response_model=Dashboard,
    dependencies=[Depends(require_api_key)],
)
def get_dashboard(company_id: str) -> Dashboard:
    try:
        return service.get_dashboard(company_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

