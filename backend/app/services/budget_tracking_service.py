"""Budget tracking service for NDIS CRM."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invoice import Invoice
from app.models.invoice_line_item import InvoiceLineItem
from app.models.participant import Participant
from app.models.plan import Plan
from app.models.support_category import SupportCategory
from app.schemas.budget import (
    BudgetAlert,
    BurnRate,
    ParticipantBudgetOverview,
    PlanBudgetSummary,
    SupportCategoryBudgetStatus,
)

_ALERT_WARN_THRESHOLD = Decimal("75")
_ALERT_CRITICAL_THRESHOLD = Decimal("90")
_UNDERSPENT_THRESHOLD = Decimal("20")
_PLAN_EXPIRING_DAYS = 30
_UNDERSPENT_PLAN_DAYS = 60


def _today() -> date:
    return datetime.now(tz=timezone.utc).date()


async def _get_plan(db: AsyncSession, plan_id: uuid.UUID) -> Plan | None:
    result = await db.execute(
        select(Plan)
        .options(selectinload(Plan.support_categories))
        .where(Plan.id == plan_id)
    )
    return result.scalar_one_or_none()


def _category_alert_level(utilisation: Decimal, is_overspent: bool) -> str | None:
    if is_overspent:
        return "overspent"
    if utilisation >= _ALERT_CRITICAL_THRESHOLD:
        return "critical"
    if utilisation >= _ALERT_WARN_THRESHOLD:
        return "warning"
    return None


async def get_plan_budget_summary(
    db: AsyncSession, plan_id: uuid.UUID
) -> PlanBudgetSummary | None:
    """Aggregate real-time budget status for a plan."""
    plan = await _get_plan(db, plan_id)
    if plan is None:
        return None

    today = _today()
    days_remaining = max((plan.plan_end_date - today).days, 0)

    burn_rates = {
        br.category_id: br
        for br in await _calculate_all_burn_rates(db, plan_id, plan.support_categories)
    }

    total_allocated = Decimal("0")
    total_spent = Decimal("0")
    categories: list[SupportCategoryBudgetStatus] = []

    for cat in plan.support_categories:
        util = Decimal(str(cat.utilisation_percent))
        alert_level = _category_alert_level(util, cat.is_overspent)
        br = burn_rates.get(cat.id)

        categories.append(
            SupportCategoryBudgetStatus(
                category_id=cat.id,
                ndis_support_category=cat.ndis_support_category,
                budget_allocated=cat.budget_allocated,
                budget_spent=cat.budget_spent,
                budget_remaining=cat.budget_remaining,
                utilisation_percent=cat.utilisation_percent,
                is_overspent=cat.is_overspent,
                burn_rate_weekly=br.avg_weekly_spend if br else None,
                projected_exhaustion_date=(
                    br.projected_exhaustion_date if br else None
                ),
                alert_level=alert_level,
            )
        )

        total_allocated += cat.budget_allocated
        total_spent += cat.budget_spent

    total_remaining = total_allocated - total_spent
    overall_util = (
        float(total_spent / total_allocated * 100) if total_allocated else 0.0
    )

    alerts = await check_budget_alerts(db, plan_id)

    return PlanBudgetSummary(
        plan_id=plan.id,
        participant_id=plan.participant_id,
        plan_start_date=plan.plan_start_date,
        plan_end_date=plan.plan_end_date,
        days_remaining=days_remaining,
        total_allocated=total_allocated,
        total_spent=total_spent,
        total_remaining=total_remaining,
        overall_utilisation_percent=overall_util,
        categories=categories,
        alerts=alerts,
    )


async def get_participant_budget_overview(
    db: AsyncSession, participant_id: uuid.UUID
) -> ParticipantBudgetOverview | None:
    """Budget summary across ALL plans for a participant (current plan highlighted)."""
    participant_result = await db.execute(
        select(Participant).where(Participant.id == participant_id)
    )
    if participant_result.scalar_one_or_none() is None:
        return None

    today = _today()
    result = await db.execute(
        select(Plan)
        .options(selectinload(Plan.support_categories))
        .where(Plan.participant_id == participant_id)
        .order_by(Plan.plan_start_date.desc())
    )
    plans: Sequence[Plan] = result.scalars().all()

    current_plan_summary: PlanBudgetSummary | None = None
    historical: list[dict] = []

    for plan in plans:
        is_current = plan.is_active and plan.plan_start_date <= today <= plan.plan_end_date
        if is_current and current_plan_summary is None:
            current_plan_summary = await get_plan_budget_summary(db, plan.id)
        else:
            total_allocated = sum(
                (c.budget_allocated for c in plan.support_categories), Decimal("0")
            )
            total_spent = sum(
                (c.budget_spent for c in plan.support_categories), Decimal("0")
            )
            historical.append(
                {
                    "plan_id": str(plan.id),
                    "plan_start_date": plan.plan_start_date.isoformat(),
                    "plan_end_date": plan.plan_end_date.isoformat(),
                    "total_allocated": str(total_allocated),
                    "total_spent": str(total_spent),
                    "is_active": plan.is_active,
                }
            )

    return ParticipantBudgetOverview(
        participant_id=participant_id,
        current_plan=current_plan_summary,
        historical_plans=historical,
    )


async def calculate_burn_rate(
    db: AsyncSession, plan_id: uuid.UUID, category_id: uuid.UUID
) -> BurnRate | None:
    """Calculate weekly/monthly spend rate for a support category."""
    cat_result = await db.execute(
        select(SupportCategory).where(
            SupportCategory.id == category_id,
            SupportCategory.plan_id == plan_id,
        )
    )
    cat = cat_result.scalar_one_or_none()
    if cat is None:
        return None

    thirty_days_ago = _today() - timedelta(days=30)
    result = await db.execute(
        select(func.coalesce(func.sum(InvoiceLineItem.total), Decimal("0")))
        .join(Invoice, InvoiceLineItem.invoice_id == Invoice.id)
        .where(
            InvoiceLineItem.support_category_id == category_id,
            Invoice.status == "approved",
            Invoice.invoice_date >= thirty_days_ago,
        )
    )
    spend_30d: Decimal = result.scalar_one()

    avg_weekly = (spend_30d / Decimal("30") * Decimal("7")).quantize(Decimal("0.01"))
    avg_monthly = spend_30d.quantize(Decimal("0.01"))

    weeks_remaining: float | None = None
    projected_exhaustion: date | None = None

    if avg_weekly > 0:
        remaining = cat.budget_remaining
        if remaining > 0:
            weeks_remaining = float(remaining / avg_weekly)
            days_until_exhaustion = int(weeks_remaining * 7)
            projected_exhaustion = _today() + timedelta(days=days_until_exhaustion)
        else:
            weeks_remaining = 0.0

    return BurnRate(
        category_id=category_id,
        avg_weekly_spend=avg_weekly,
        avg_monthly_spend=avg_monthly,
        weeks_remaining_at_current_rate=weeks_remaining,
        projected_exhaustion_date=projected_exhaustion,
    )


async def _calculate_all_burn_rates(
    db: AsyncSession,
    plan_id: uuid.UUID,
    categories: Sequence[SupportCategory],
) -> list[BurnRate]:
    """Calculate burn rates for all categories in a plan."""
    results = []
    for cat in categories:
        br = await calculate_burn_rate(db, plan_id, cat.id)
        if br is not None:
            results.append(br)
    return results


async def check_budget_alerts(
    db: AsyncSession, plan_id: uuid.UUID
) -> list[BudgetAlert]:
    """Generate budget alerts for a plan."""
    plan = await _get_plan(db, plan_id)
    if plan is None:
        return []

    alerts: list[BudgetAlert] = []
    today = _today()
    days_remaining = (plan.plan_end_date - today).days

    if days_remaining < _PLAN_EXPIRING_DAYS:
        alerts.append(
            BudgetAlert(
                alert_type="PLAN_EXPIRING",
                category_id=None,
                category_name=None,
                message=(
                    f"Plan expires in {days_remaining} day(s) "
                    f"(end date: {plan.plan_end_date})."
                ),
                severity="warning",
            )
        )

    for cat in plan.support_categories:
        util = Decimal(str(cat.utilisation_percent))

        if cat.is_overspent:
            alerts.append(
                BudgetAlert(
                    alert_type="OVERSPENT",
                    category_id=cat.id,
                    category_name=cat.ndis_support_category,
                    message=(
                        f"{cat.ndis_support_category} is overspent: "
                        f"spent ${cat.budget_spent} of ${cat.budget_allocated} allocated."
                    ),
                    severity="critical",
                )
            )
        elif util >= _ALERT_CRITICAL_THRESHOLD:
            alerts.append(
                BudgetAlert(
                    alert_type="CRITICAL",
                    category_id=cat.id,
                    category_name=cat.ndis_support_category,
                    message=(
                        f"{cat.ndis_support_category} is at "
                        f"{cat.utilisation_percent:.1f}% utilisation (critical threshold)."
                    ),
                    severity="critical",
                )
            )
        elif util >= _ALERT_WARN_THRESHOLD:
            alerts.append(
                BudgetAlert(
                    alert_type="WARNING",
                    category_id=cat.id,
                    category_name=cat.ndis_support_category,
                    message=(
                        f"{cat.ndis_support_category} is at "
                        f"{cat.utilisation_percent:.1f}% utilisation (approaching limit)."
                    ),
                    severity="warning",
                )
            )

        if (
            not cat.is_overspent
            and util < _UNDERSPENT_THRESHOLD
            and 0 < days_remaining < _UNDERSPENT_PLAN_DAYS
        ):
            alerts.append(
                BudgetAlert(
                    alert_type="UNDERSPENT",
                    category_id=cat.id,
                    category_name=cat.ndis_support_category,
                    message=(
                        f"{cat.ndis_support_category} is only {cat.utilisation_percent:.1f}% "
                        f"utilised with {days_remaining} day(s) remaining in the plan."
                    ),
                    severity="info",
                )
            )

    return alerts


async def recalculate_budget_spent(db: AsyncSession, plan_id: uuid.UUID) -> None:
    """Recalculate budget_spent for all categories from approved invoices."""
    plan = await _get_plan(db, plan_id)
    if plan is None:
        return

    for cat in plan.support_categories:
        result = await db.execute(
            select(func.coalesce(func.sum(InvoiceLineItem.total), Decimal("0")))
            .join(Invoice, InvoiceLineItem.invoice_id == Invoice.id)
            .where(
                InvoiceLineItem.support_category_id == cat.id,
                Invoice.status == "approved",
            )
        )
        cat.budget_spent = result.scalar_one()

    await db.commit()


async def get_all_active_plan_alerts(
    db: AsyncSession, severity: str | None = None
) -> list[BudgetAlert]:
    """Get budget alerts across all active plans (coordinator dashboard view)."""
    today = _today()
    result = await db.execute(
        select(Plan)
        .options(selectinload(Plan.support_categories))
        .where(Plan.is_active.is_(True))
    )
    plans: Sequence[Plan] = result.scalars().all()

    all_alerts: list[BudgetAlert] = []
    for plan in plans:
        alerts = await check_budget_alerts(db, plan.id)
        all_alerts.extend(alerts)

    if severity is not None:
        all_alerts = [a for a in all_alerts if a.severity == severity]

    return all_alerts
