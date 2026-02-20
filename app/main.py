import os

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


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
