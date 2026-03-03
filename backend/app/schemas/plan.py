"""Pydantic v2 schemas for Plan endpoints."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.support_category import SupportCategoryOut


class PlanBase(BaseModel):
    plan_start_date: date
    plan_end_date: date
    total_funding: Decimal
    plan_manager: str | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_dates(self) -> PlanBase:
        if self.plan_end_date <= self.plan_start_date:
            raise ValueError("plan_end_date must be after plan_start_date")
        return self


class PlanIn(PlanBase):
    participant_id: UUID


class PlanUpdate(BaseModel):
    plan_start_date: date | None = None
    plan_end_date: date | None = None
    total_funding: Decimal | None = None
    plan_manager: str | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> PlanUpdate:
        if self.plan_start_date and self.plan_end_date:
            if self.plan_end_date <= self.plan_start_date:
                raise ValueError("plan_end_date must be after plan_start_date")
        return self


class PlanOut(PlanBase):
    id: UUID
    participant_id: UUID
    created_at: datetime
    updated_at: datetime
    support_categories: list[SupportCategoryOut] = []

    model_config = ConfigDict(from_attributes=True)


class PlanListOut(BaseModel):
    items: list[PlanOut]
    total: int
    page: int
    page_size: int
