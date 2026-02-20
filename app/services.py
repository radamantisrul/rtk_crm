from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.schemas import (
    Automation,
    AutomationCreate,
    Company,
    CompanyCreate,
    Customer,
    CustomerCreate,
    CustomerStatus,
    CustomerStatusChange,
    Dashboard,
    Integration,
    IntegrationCreate,
)


@dataclass
class UISPClient:
    """Stub de integración UISP para activación/suspensión."""

    company_id: str

    def sync_customer_status(self, customer_id: str, status: CustomerStatus, reason: str | None = None) -> dict:
        return {
            "provider": "uisp",
            "company_id": self.company_id,
            "customer_id": customer_id,
            "status": status.value,
            "reason": reason,
            "synced": True,
        }


@dataclass
class N8NClient:
    """Stub de automatización saliente hacia n8n."""

    company_id: str

    def trigger(self, webhook: str, payload: dict) -> dict:
        return {
            "provider": "n8n",
            "company_id": self.company_id,
            "webhook": webhook,
            "payload": payload,
            "queued": True,
        }


@dataclass
class CompanyData:
    company: Company
    integrations: dict[str, Integration] = field(default_factory=dict)
    automations: dict[str, Automation] = field(default_factory=dict)
    customers: dict[str, Customer] = field(default_factory=dict)


class CRMService:
    def __init__(self) -> None:
        self.companies: dict[str, CompanyData] = {}

    def create_company(self, payload: CompanyCreate) -> Company:
        if payload.parent_company_id and payload.parent_company_id not in self.companies:
            raise ValueError("parent_company_id no existe")
        company = Company(id=str(uuid4()), **payload.model_dump())
        self.companies[company.id] = CompanyData(company=company)
        return company

    def list_companies(self) -> list[Company]:
        return [entry.company for entry in self.companies.values()]

    def _require_company(self, company_id: str) -> CompanyData:
        company_data = self.companies.get(company_id)
        if not company_data:
            raise KeyError("company no encontrada")
        return company_data

    def create_integration(self, company_id: str, payload: IntegrationCreate) -> Integration:
        company_data = self._require_company(company_id)
        integration = Integration(id=str(uuid4()), **payload.model_dump())
        company_data.integrations[integration.id] = integration
        return integration

    def create_automation(self, company_id: str, payload: AutomationCreate) -> Automation:
        company_data = self._require_company(company_id)
        automation = Automation(id=str(uuid4()), **payload.model_dump())
        company_data.automations[automation.id] = automation
        return automation

    def create_customer(self, company_id: str, payload: CustomerCreate) -> Customer:
        company_data = self._require_company(company_id)
        customer = Customer(id=str(uuid4()), **payload.model_dump())
        company_data.customers[customer.id] = customer
        return customer

    def change_customer_status(self, company_id: str, customer_id: str, payload: CustomerStatusChange) -> dict:
        company_data = self._require_company(company_id)
        customer = company_data.customers.get(customer_id)
        if not customer:
            raise KeyError("customer no encontrado")

        updated = customer.model_copy(update={"status": payload.status})
        company_data.customers[customer_id] = updated

        uisp_response = UISPClient(company_id=company_id).sync_customer_status(
            customer_id=customer_id,
            status=payload.status,
            reason=payload.reason,
        )

        automation_runs: list[dict] = []
        event_name = "customer.status_changed"
        n8n = N8NClient(company_id=company_id)

        for automation in company_data.automations.values():
            if automation.enabled and automation.event == event_name:
                payload_data = {
                    "event": event_name,
                    "company_id": company_id,
                    "customer_id": customer_id,
                    "status": payload.status.value,
                    "reason": payload.reason,
                }
                automation_runs.append(n8n.trigger(str(automation.target_webhook), payload_data))

        return {
            "customer": updated,
            "uisp": uisp_response,
            "automations": automation_runs,
        }

    def get_dashboard(self, company_id: str) -> Dashboard:
        company_data = self._require_company(company_id)
        customers = list(company_data.customers.values())

        active = sum(1 for c in customers if c.status == CustomerStatus.ACTIVE)
        suspended = sum(1 for c in customers if c.status == CustomerStatus.SUSPENDED)
        integration_types = [integration.type for integration in company_data.integrations.values()]
        enabled_automations = sum(1 for automation in company_data.automations.values() if automation.enabled)

        return Dashboard(
            total_customers=len(customers),
            active_customers=active,
            suspended_customers=suspended,
            integrations=integration_types,
            automations_enabled=enabled_automations,
        )
