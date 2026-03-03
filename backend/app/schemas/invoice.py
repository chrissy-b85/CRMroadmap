"""Pydantic v2 schemas for Invoice endpoints."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InvoiceLineItemOut(BaseModel):
    id: UUID
    invoice_id: UUID
    description: str | None = None
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
    support_item_number: str | None = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceOut(BaseModel):
    id: UUID
    participant_id: UUID | None = None
    provider_id: UUID | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    total_amount: Decimal
    gst_amount: Decimal
    status: str
    ocr_confidence: float | None = None
    gcs_pdf_path: str | None = None
    gcs_json_path: str | None = None
    line_items: list[InvoiceLineItemOut] = []
    created_at: datetime
    participant_approved: bool | None = None
    participant_approved_at: datetime | None = None
    participant_query_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceListOut(BaseModel):
    items: list[InvoiceOut]
    total: int
    page: int
    page_size: int
