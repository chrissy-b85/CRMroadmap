"""Pydantic v2 schemas for SupportCategory endpoints."""
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SupportCategoryIn(BaseModel):
    ndis_support_category: str
    budget_allocated: Decimal


class SupportCategoryUpdate(BaseModel):
    ndis_support_category: str | None = None
    budget_allocated: Decimal | None = None
    budget_spent: Decimal | None = None


class SupportCategoryOut(SupportCategoryIn):
    id: UUID
    plan_id: UUID
    budget_spent: Decimal
    budget_remaining: Decimal

    model_config = ConfigDict(from_attributes=True)
