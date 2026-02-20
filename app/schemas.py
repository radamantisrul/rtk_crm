from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    name: str = Field(min_length=2)
    network_name: str = Field(min_length=2)


class TenantUpdate(BaseModel):
    name: str = Field(min_length=2)
    network_name: str = Field(min_length=2)


class TenantOut(BaseModel):
    id: str
    name: str
    network_name: str

    model_config = {"from_attributes": True}


class CustomerCreate(BaseModel):
    name: str = Field(min_length=2)
    email: str
    plan_name: str
    status: str = "active"


class CustomerUpdate(BaseModel):
    name: str = Field(min_length=2)
    email: str
    plan_name: str
    status: str = "active"


class CustomerOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    email: str
    plan_name: str
    status: str

    model_config = {"from_attributes": True}


class IntegrationCreate(BaseModel):
    provider: str
    config: dict[str, Any]


class IntegrationOut(BaseModel):
    id: str
    tenant_id: str
    provider: str
    config_keys: list[str]


class IntegrationTestResult(BaseModel):
    ok: bool
    status_code: int | None = None
    detail: str
