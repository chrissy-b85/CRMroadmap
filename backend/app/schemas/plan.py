"""Pydantic v2 schemas for Plan endpoints."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlanIn(BaseModel):
    plan_start_date: date
    plan_end_date: date
    total_funding: Decimal
    plan_manager: str | None = None


class PlanOut(PlanIn):
    id: UUID
    participant_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
