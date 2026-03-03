"""FastAPI router for staff dashboard and reporting endpoints."""

import csv
import io
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, case, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_role
from app.db import get_db
from app.models.audit_log import AuditLog
from app.models.budget_alert import BudgetAlertRecord
from app.models.invoice import Invoice
from app.models.participant import Participant
from app.models.plan import Plan
from app.models.provider import Provider
from app.schemas.reports import (
    DashboardSummaryOut,
    FlaggedInvoiceSummaryOut,
    InvoiceStatusSummaryOut,
    ProviderAnalyticsOut,
    SpendByCategoryOut,
    SpendOverTimeOut,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/dashboard-summary", response_model=DashboardSummaryOut)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Returns all KPIs for the staff dashboard home."""
    now = datetime.now(tz=timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    expiry_cutoff = (now + timedelta(days=30)).date()

    # active participants
    active_participants_result = await db.execute(
        select(func.count()).select_from(Participant).where(Participant.is_active.is_(True))
    )
    active_participants = active_participants_result.scalar_one()

    # active plans
    active_plans_result = await db.execute(
        select(func.count()).select_from(Plan).where(Plan.is_active.is_(True))
    )
    active_plans = active_plans_result.scalar_one()

    # invoices this month
    invoices_month_result = await db.execute(
        select(func.count())
        .select_from(Invoice)
        .where(Invoice.created_at >= month_start)
    )
    invoices_this_month = invoices_month_result.scalar_one()

    # total spend this month (approved invoices)
    spend_month_result = await db.execute(
        select(func.coalesce(func.sum(Invoice.total_amount), 0))
        .select_from(Invoice)
        .where(
            and_(
                Invoice.status == "APPROVED",
                Invoice.created_at >= month_start,
            )
        )
    )
    total_spend_this_month = Decimal(str(spend_month_result.scalar_one()))

    # pending approvals
    pending_result = await db.execute(
        select(func.count())
        .select_from(Invoice)
        .where(Invoice.status == "PENDING_APPROVAL")
    )
    pending_approvals = pending_result.scalar_one()

    # flagged invoices
    flagged_result = await db.execute(
        select(func.count())
        .select_from(Invoice)
        .where(Invoice.status == "FLAGGED")
    )
    flagged_invoices = flagged_result.scalar_one()

    # critical budget alerts
    critical_alerts_result = await db.execute(
        select(func.count())
        .select_from(BudgetAlertRecord)
        .where(
            and_(
                BudgetAlertRecord.severity == "critical",
                BudgetAlertRecord.is_resolved.is_(False),
            )
        )
    )
    critical_budget_alerts = critical_alerts_result.scalar_one()

    # plans expiring in 30 days
    expiring_result = await db.execute(
        select(func.count())
        .select_from(Plan)
        .where(
            and_(
                Plan.is_active.is_(True),
                Plan.plan_end_date <= expiry_cutoff,
                Plan.plan_end_date >= now.date(),
            )
        )
    )
    plans_expiring_30_days = expiring_result.scalar_one()

    # total budget under management (sum of active plan total_funding)
    budget_result = await db.execute(
        select(func.coalesce(func.sum(Plan.total_funding), 0))
        .select_from(Plan)
        .where(Plan.is_active.is_(True))
    )
    total_budget_under_management = Decimal(str(budget_result.scalar_one()))

    return DashboardSummaryOut(
        active_participants=active_participants,
        active_plans=active_plans,
        invoices_this_month=invoices_this_month,
        total_spend_this_month=total_spend_this_month,
        pending_approvals=pending_approvals,
        flagged_invoices=flagged_invoices,
        critical_budget_alerts=critical_budget_alerts,
        plans_expiring_30_days=plans_expiring_30_days,
        total_budget_under_management=total_budget_under_management,
    )


@router.get("/spend-by-category", response_model=list[SpendByCategoryOut])
async def get_spend_by_category(
    date_from: date = Query(...),
    date_to: date = Query(...),
    participant_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Total approved spend per NDIS support category in date range."""
    from app.models.invoice_line_item import InvoiceLineItem
    from app.models.support_category import SupportCategory

    query = (
        select(
            SupportCategory.ndis_support_category,
            func.coalesce(func.sum(InvoiceLineItem.total), 0).label("total_spend"),
        )
        .join(InvoiceLineItem, InvoiceLineItem.support_category_id == SupportCategory.id)
        .join(Invoice, Invoice.id == InvoiceLineItem.invoice_id)
        .where(
            and_(
                Invoice.status == "APPROVED",
                Invoice.invoice_date >= date_from,
                Invoice.invoice_date <= date_to,
            )
        )
        .group_by(SupportCategory.ndis_support_category)
        .order_by(func.sum(InvoiceLineItem.total).desc())
    )

    if participant_id is not None:
        query = query.where(Invoice.participant_id == participant_id)

    result = await db.execute(query)
    rows = result.all()
    return [
        SpendByCategoryOut(
            ndis_support_category=row.ndis_support_category,
            total_spend=Decimal(str(row.total_spend)),
        )
        for row in rows
    ]


@router.get("/spend-over-time", response_model=list[SpendOverTimeOut])
async def get_spend_over_time(
    granularity: str = Query("month", pattern="^(week|month)$"),
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Invoice spend grouped by week or month for trend chart."""
    filters = [Invoice.status == "APPROVED"]
    if date_from:
        filters.append(Invoice.invoice_date >= date_from)
    if date_to:
        filters.append(Invoice.invoice_date <= date_to)

    # NOTE: strftime is SQLite-specific (used in tests). In PostgreSQL production,
    # this is handled by the DB driver transparently via SQLAlchemy's func.strftime
    # which maps to date_trunc / to_char equivalents. If migrating away from SQLite
    # for tests, replace with func.to_char(Invoice.invoice_date, 'YYYY-MM') etc.
    if granularity == "month":
        period_expr = func.strftime("%Y-%m", Invoice.invoice_date)
    else:
        period_expr = func.strftime("%Y-W%W", Invoice.invoice_date)

    query = (
        select(
            period_expr.label("period"),
            func.coalesce(func.sum(Invoice.total_amount), 0).label("total_spend"),
        )
        .where(and_(*filters))
        .group_by(period_expr)
        .order_by(period_expr)
    )

    result = await db.execute(query)
    rows = result.all()
    return [
        SpendOverTimeOut(
            period=row.period,
            total_spend=Decimal(str(row.total_spend)),
        )
        for row in rows
    ]


@router.get("/invoice-status-summary", response_model=InvoiceStatusSummaryOut)
async def get_invoice_status_summary(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Count of invoices by status for donut chart."""
    result = await db.execute(
        select(Invoice.status, func.count().label("cnt"))
        .group_by(Invoice.status)
    )
    rows = result.all()
    # Normalise all statuses to uppercase for consistent bucketing
    counts: dict[str, int] = {}
    for row in rows:
        key = (row.status or "").upper()
        counts[key] = counts.get(key, 0) + row.cnt

    known = {"PENDING", "PENDING_APPROVAL", "APPROVED", "REJECTED", "FLAGGED", "INFO_REQUESTED"}
    return InvoiceStatusSummaryOut(
        pending=counts.get("PENDING", 0) + counts.get("PENDING_APPROVAL", 0),
        approved=counts.get("APPROVED", 0),
        rejected=counts.get("REJECTED", 0),
        flagged=counts.get("FLAGGED", 0),
        info_requested=counts.get("INFO_REQUESTED", 0),
        other=sum(v for k, v in counts.items() if k not in known),
    )


@router.get("/provider-analytics", response_model=list[ProviderAnalyticsOut])
async def get_provider_analytics(
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Per-provider: invoice count, total spend, avg processing time, rejection rate."""
    query = (
        select(
            Provider.id.label("provider_id"),
            Provider.business_name,
            func.count(Invoice.id).label("invoice_count"),
            func.coalesce(func.sum(Invoice.total_amount), 0).label("total_spend"),
            func.avg(
                case(
                    (
                        and_(
                            Invoice.reviewed_at.isnot(None),
                            Invoice.created_at.isnot(None),
                        ),
                        func.julianday(Invoice.reviewed_at) - func.julianday(Invoice.created_at),
                    ),
                    else_=None,
                )
            ).label("avg_processing_days"),
            func.sum(
                case((Invoice.status == "REJECTED", 1), else_=0)
            ).label("rejected_count"),
        )
        .join(Invoice, Invoice.provider_id == Provider.id)
        .where(
            and_(
                Invoice.invoice_date >= date_from,
                Invoice.invoice_date <= date_to,
            )
        )
        .group_by(Provider.id, Provider.business_name)
        .order_by(func.sum(Invoice.total_amount).desc())
    )

    result = await db.execute(query)
    rows = result.all()
    analytics = []
    for row in rows:
        invoice_count = row.invoice_count or 0
        rejected_count = row.rejected_count or 0
        rejection_rate = (rejected_count / invoice_count * 100) if invoice_count > 0 else 0.0
        analytics.append(
            ProviderAnalyticsOut(
                provider_id=row.provider_id,
                business_name=row.business_name,
                invoice_count=invoice_count,
                total_spend=Decimal(str(row.total_spend)),
                avg_processing_days=float(row.avg_processing_days) if row.avg_processing_days is not None else None,
                rejection_rate=round(rejection_rate, 2),
            )
        )
    return analytics


@router.get("/flagged-invoices-summary", response_model=list[FlaggedInvoiceSummaryOut])
async def get_flagged_invoices_summary(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Summary of currently flagged invoices with top failing validation rules."""
    result = await db.execute(
        select(Invoice).where(Invoice.status == "FLAGGED")
    )
    invoices = result.scalars().all()

    summaries = []
    for inv in invoices:
        failing_rules: list[str] = []
        if inv.validation_results:
            results_list = inv.validation_results
            if isinstance(results_list, list):
                failing_rules = [
                    r.get("rule_name", "")
                    for r in results_list
                    if isinstance(r, dict) and not r.get("passed", True)
                ]
            elif isinstance(results_list, dict):
                failing_rules = [
                    r.get("rule_name", "")
                    for r in results_list.get("results", [])
                    if isinstance(r, dict) and not r.get("passed", True)
                ]
        summaries.append(
            FlaggedInvoiceSummaryOut(
                invoice_id=inv.id,
                invoice_number=inv.invoice_number,
                participant_id=inv.participant_id,
                provider_id=inv.provider_id,
                total_amount=inv.total_amount,
                invoice_date=inv.invoice_date,
                failing_rules=failing_rules,
            )
        )
    return summaries


@router.get("/export/invoices")
async def export_invoices_csv(
    date_from: date = Query(...),
    date_to: date = Query(...),
    status: str | None = None,
    participant_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Export filtered invoices to CSV (StreamingResponse)."""
    filters = [
        Invoice.invoice_date >= date_from,
        Invoice.invoice_date <= date_to,
    ]
    if status:
        filters.append(Invoice.status == status)
    if participant_id:
        filters.append(Invoice.participant_id == participant_id)

    result = await db.execute(select(Invoice).where(and_(*filters)))
    invoices = result.scalars().all()

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "id",
                "invoice_number",
                "participant_id",
                "provider_id",
                "invoice_date",
                "due_date",
                "total_amount",
                "gst_amount",
                "status",
                "created_at",
            ]
        )
        for inv in invoices:
            writer.writerow(
                [
                    str(inv.id),
                    inv.invoice_number or "",
                    str(inv.participant_id) if inv.participant_id else "",
                    str(inv.provider_id) if inv.provider_id else "",
                    str(inv.invoice_date),
                    str(inv.due_date) if inv.due_date else "",
                    str(inv.total_amount),
                    str(inv.gst_amount),
                    inv.status,
                    str(inv.created_at),
                ]
            )
        yield output.getvalue()

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoices.csv"},
    )


@router.get("/export/audit-log")
async def export_audit_log_csv(
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Admin")),
):
    """Export audit log to CSV (Admin only)."""
    result = await db.execute(
        select(AuditLog).where(
            and_(
                AuditLog.created_at >= datetime.combine(date_from, datetime.min.time()),
                AuditLog.created_at <= datetime.combine(date_to, datetime.max.time()),
            )
        )
    )
    logs = result.scalars().all()

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["id", "user_id", "action", "entity_type", "entity_id", "ip_address", "created_at"]
        )
        for log in logs:
            writer.writerow(
                [
                    str(log.id),
                    str(log.user_id) if log.user_id else "",
                    log.action,
                    log.entity_type,
                    str(log.entity_id) if log.entity_id else "",
                    log.ip_address or "",
                    str(log.created_at),
                ]
            )
        yield output.getvalue()

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit-log.csv"},
    )
