"""Pydantic models for Xero API responses."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class XeroBill(BaseModel):
    xero_invoice_id: str
    invoice_number: str
    status: str  # DRAFT, SUBMITTED, AUTHORISED, PAID, VOIDED
    amount_due: Decimal
    amount_paid: Decimal
    contact_id: str


class XeroContact(BaseModel):
    contact_id: str
    name: str
    tax_number: str | None = None  # ABN


class XeroTokens(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int  # seconds
