"""Pydantic v2 schemas for budget tracking endpoints."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SupportCategoryBudgetStatus(BaseModel):
    category_id: UUID
    ndis_support_category: str
    budget_allocated: Decimal
    budget_spent: Decimal
    budget_remaining: Decimal
    utilisation_percent: float
    is_overspent: bool
    burn_rate_weekly: Decimal | None = None
    projected_exhaustion_date: date | None = None
    alert_level: str | None = None  # None | "warning" | "critical" | "overspent"

    model_config = ConfigDict(from_attributes=True)


class BudgetAlert(BaseModel):
    alert_type: str  # WARNING | CRITICAL | OVERSPENT | PLAN_EXPIRING | UNDERSPENT
    category_id: UUID | None = None
    category_name: str | None = None
    message: str
    severity: str  # info | warning | critical

    model_config = ConfigDict(from_attributes=True)


class BurnRate(BaseModel):
    category_id: UUID
    avg_weekly_spend: Decimal
    avg_monthly_spend: Decimal
    weeks_remaining_at_current_rate: float | None = None
    projected_exhaustion_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


class PlanBudgetSummary(BaseModel):
    plan_id: UUID
    participant_id: UUID
    plan_start_date: date
    plan_end_date: date
    days_remaining: int
    total_allocated: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    overall_utilisation_percent: float
    categories: list[SupportCategoryBudgetStatus]
    alerts: list[BudgetAlert]

    model_config = ConfigDict(from_attributes=True)


class ParticipantBudgetOverview(BaseModel):
    participant_id: UUID
    current_plan: PlanBudgetSummary | None = None
    historical_plans: list[dict] = []

    model_config = ConfigDict(from_attributes=True)
