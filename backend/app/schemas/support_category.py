"""Pydantic v2 schemas for SupportCategory endpoints."""
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field


class SupportCategoryIn(BaseModel):
    ndis_support_category: str
    ndis_support_number: str | None = None
    budget_allocated: Decimal
    budget_spent: Decimal = Decimal("0.00")


class SupportCategoryUpdate(BaseModel):
    ndis_support_category: str | None = None
    ndis_support_number: str | None = None
    budget_allocated: Decimal | None = None
    budget_spent: Decimal | None = None


class SupportCategoryOut(BaseModel):
    id: UUID
    plan_id: UUID
    ndis_support_category: str
    ndis_support_number: str | None
    budget_allocated: Decimal
    budget_spent: Decimal
    budget_remaining: Decimal
    utilisation_percent: float
    is_overspent: bool

    model_config = ConfigDict(from_attributes=True)


class BudgetSummaryOut(BaseModel):
    plan_id: UUID
    total_allocated: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    overall_utilisation_percent: float
    categories: list[SupportCategoryOut]
