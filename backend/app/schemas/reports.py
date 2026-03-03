"""Pydantic v2 output schemas for the reporting endpoints."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DashboardSummaryOut(BaseModel):
    active_participants: int
    active_plans: int
    invoices_this_month: int
    total_spend_this_month: Decimal
    pending_approvals: int
    flagged_invoices: int
    critical_budget_alerts: int
    plans_expiring_30_days: int
    total_budget_under_management: Decimal


class SpendByCategoryOut(BaseModel):
    ndis_support_category: str
    total_spend: Decimal

    model_config = ConfigDict(from_attributes=True)


class SpendOverTimeOut(BaseModel):
    period: str  # "2024-01" for monthly, "2024-W03" for weekly
    total_spend: Decimal

    model_config = ConfigDict(from_attributes=True)


class InvoiceStatusSummaryOut(BaseModel):
    pending: int
    approved: int
    rejected: int
    flagged: int
    info_requested: int
    other: int


class ProviderAnalyticsOut(BaseModel):
    provider_id: UUID
    business_name: str
    invoice_count: int
    total_spend: Decimal
    avg_processing_days: float | None
    rejection_rate: float

    model_config = ConfigDict(from_attributes=True)


class FlaggedInvoiceSummaryOut(BaseModel):
    invoice_id: UUID
    invoice_number: str | None
    participant_id: UUID | None
    provider_id: UUID | None
    total_amount: Decimal
    invoice_date: date
    failing_rules: list[str]

    model_config = ConfigDict(from_attributes=True)
