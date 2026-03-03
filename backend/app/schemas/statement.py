"""Pydantic v2 schemas for Statement endpoints."""

from calendar import month_name as _month_name
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field


class StatementOut(BaseModel):
    id: UUID
    participant_id: UUID
    year: int
    month: int
    gcs_pdf_path: str
    download_url: str
    invoice_count: int
    total_amount: Decimal
    generated_at: datetime
    emailed_at: datetime | None = None

    @computed_field  # type: ignore[misc]
    @property
    def statement_period(self) -> str:
        """Human-readable period, e.g. 'February 2026'."""
        return f"{_month_name[self.month]} {self.year}"

    model_config = ConfigDict(from_attributes=True)
