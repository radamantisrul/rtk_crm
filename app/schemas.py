from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class CustomerStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class IntegrationType(str, Enum):
    UISP = "uisp"
    OPENAI = "openai"
    N8N = "n8n"
    GOOGLE = "google"


class CompanyCreate(BaseModel):
    name: str = Field(min_length=2)
    network_name: str = Field(min_length=2)
    parent_company_id: str | None = None


class Company(BaseModel):
    id: str
    name: str
    network_name: str
    parent_company_id: str | None = None


class IntegrationCreate(BaseModel):
    type: IntegrationType
    config: dict[str, Any]


class Integration(BaseModel):
    id: str
    type: IntegrationType
    config: dict[str, Any]


class AutomationCreate(BaseModel):
    name: str
    event: str = Field(description="Ejemplo: customer.status_changed")
    enabled: bool = True
    target_webhook: HttpUrl


class Automation(BaseModel):
    id: str
    name: str
    event: str
    enabled: bool
    target_webhook: HttpUrl


class CustomerCreate(BaseModel):
    name: str = Field(min_length=2)
    email: str
    plan_name: str


class Customer(BaseModel):
    id: str
    name: str
    email: str
    plan_name: str
    status: CustomerStatus = CustomerStatus.ACTIVE


class CustomerStatusChange(BaseModel):
    status: CustomerStatus
    reason: str | None = None


class Dashboard(BaseModel):
    total_customers: int
    active_customers: int
    suspended_customers: int
    integrations: list[IntegrationType]
    automations_enabled: int
