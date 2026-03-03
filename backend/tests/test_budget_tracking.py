"""Tests for budget tracking service and API endpoints."""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice
from app.models.invoice_line_item import InvoiceLineItem
from app.models.participant import Participant
from app.models.plan import Plan
from app.models.support_category import SupportCategory
from app.services import budget_tracking_service as svc
from tests.conftest import make_participant_payload

pytestmark = pytest.mark.asyncio

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TODAY = date.today()


async def _make_plan(
    db: AsyncSession,
    start: date | None = None,
    end: date | None = None,
    is_active: bool = True,
) -> tuple[Participant, Plan]:
    participant = Participant(
        ndis_number=f"NDIS{uuid.uuid4().hex[:8].upper()}",
        first_name="Test",
        last_name="User",
        date_of_birth=date(1990, 1, 1),
        email=f"test_{uuid.uuid4().hex[:6]}@example.com",
    )
    db.add(participant)
    await db.flush()

    plan = Plan(
        participant_id=participant.id,
        plan_start_date=start or TODAY - timedelta(days=100),
        plan_end_date=end or TODAY + timedelta(days=265),
        total_funding=Decimal("50000.00"),
        is_active=is_active,
    )
    db.add(plan)
    await db.flush()
    return participant, plan


async def _make_category(
    db: AsyncSession,
    plan_id: uuid.UUID,
    name: str = "Daily Activities",
    allocated: Decimal = Decimal("10000.00"),
    spent: Decimal = Decimal("0.00"),
) -> SupportCategory:
    cat = SupportCategory(
        plan_id=plan_id,
        ndis_support_category=name,
        budget_allocated=allocated,
        budget_spent=spent,
    )
    db.add(cat)
    await db.flush()
    return cat


async def _make_approved_invoice(
    db: AsyncSession,
    participant_id: uuid.UUID,
    plan_id: uuid.UUID,
    cat_id: uuid.UUID,
    amount: Decimal,
    invoice_date: date | None = None,
) -> Invoice:
    invoice = Invoice(
        participant_id=participant_id,
        plan_id=plan_id,
        invoice_date=invoice_date or TODAY,
        total_amount=amount,
        status="approved",
    )
    db.add(invoice)
    await db.flush()

    line_item = InvoiceLineItem(
        invoice_id=invoice.id,
        unit_price=amount,
        quantity=Decimal("1"),
        total=amount,
        support_category_id=cat_id,
    )
    db.add(line_item)
    await db.flush()
    return invoice


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_get_plan_budget_summary_correct_totals(db_session: AsyncSession):
    """PlanBudgetSummary totals match the sum of support category values."""
    participant, plan = await _make_plan(db_session)
    cat1 = await _make_category(
        db_session, plan.id, "Daily Activities", Decimal("10000.00"), Decimal("3000.00")
    )
    cat2 = await _make_category(
        db_session, plan.id, "Capacity Building", Decimal("5000.00"), Decimal("1000.00")
    )
    await db_session.commit()

    summary = await svc.get_plan_budget_summary(db_session, plan.id)
    assert summary is not None
    assert summary.total_allocated == Decimal("15000.00")
    assert summary.total_spent == Decimal("4000.00")
    assert summary.total_remaining == Decimal("11000.00")
    assert len(summary.categories) == 2


async def test_utilisation_percent_calculated_correctly(db_session: AsyncSession):
    """utilisation_percent on SupportCategoryBudgetStatus matches expected value."""
    participant, plan = await _make_plan(db_session)
    await _make_category(
        db_session, plan.id, "Daily Activities", Decimal("10000.00"), Decimal("8000.00")
    )
    await db_session.commit()

    summary = await svc.get_plan_budget_summary(db_session, plan.id)
    assert summary is not None
    cat_status = summary.categories[0]
    assert abs(cat_status.utilisation_percent - 80.0) < 0.01


async def test_overspent_flag_set_correctly(db_session: AsyncSession):
    """is_overspent is True when budget_spent > budget_allocated."""
    participant, plan = await _make_plan(db_session)
    await _make_category(
        db_session, plan.id, "Daily Activities", Decimal("5000.00"), Decimal("6000.00")
    )
    await db_session.commit()

    summary = await svc.get_plan_budget_summary(db_session, plan.id)
    assert summary is not None
    assert summary.categories[0].is_overspent is True
    assert summary.categories[0].alert_level == "overspent"


async def test_burn_rate_calculation(db_session: AsyncSession):
    """avg_weekly_spend reflects approved invoices in the last 30 days."""
    participant, plan = await _make_plan(db_session)
    cat = await _make_category(
        db_session, plan.id, "Capacity Building", Decimal("10000.00"), Decimal("0.00")
    )
    # Two invoices of $700 each in the last 30 days
    await _make_approved_invoice(
        db_session, participant.id, plan.id, cat.id, Decimal("700.00"),
        TODAY - timedelta(days=10)
    )
    await _make_approved_invoice(
        db_session, participant.id, plan.id, cat.id, Decimal("700.00"),
        TODAY - timedelta(days=5)
    )
    await db_session.commit()

    br = await svc.calculate_burn_rate(db_session, plan.id, cat.id)
    assert br is not None
    # spend_30d = 1400, avg_weekly = 1400/30*7 ≈ 326.67
    expected_weekly = (Decimal("1400") / Decimal("30") * Decimal("7")).quantize(Decimal("0.01"))
    assert br.avg_weekly_spend == expected_weekly
    assert br.avg_monthly_spend == Decimal("1400.00")


async def test_projected_exhaustion_date(db_session: AsyncSession):
    """projected_exhaustion_date is set when burn rate > 0 and budget remains."""
    participant, plan = await _make_plan(db_session)
    cat = await _make_category(
        db_session, plan.id, "Daily Activities", Decimal("10000.00"), Decimal("0.00")
    )
    # Spend $700 over past 30 days
    await _make_approved_invoice(
        db_session, participant.id, plan.id, cat.id, Decimal("700.00"),
        TODAY - timedelta(days=15)
    )
    await db_session.commit()

    br = await svc.calculate_burn_rate(db_session, plan.id, cat.id)
    assert br is not None
    assert br.projected_exhaustion_date is not None
    assert br.projected_exhaustion_date > TODAY


async def test_alert_generated_at_75_percent(db_session: AsyncSession):
    """A WARNING alert is generated when utilisation is >= 75%."""
    participant, plan = await _make_plan(db_session)
    await _make_category(
        db_session, plan.id, "Daily Activities", Decimal("10000.00"), Decimal("7600.00")
    )
    await db_session.commit()

    alerts = await svc.check_budget_alerts(db_session, plan.id)
    warning_alerts = [a for a in alerts if a.alert_type == "WARNING"]
    assert len(warning_alerts) == 1
    assert warning_alerts[0].severity == "warning"


async def test_alert_generated_at_90_percent(db_session: AsyncSession):
    """A CRITICAL alert is generated when utilisation is >= 90%."""
    participant, plan = await _make_plan(db_session)
    await _make_category(
        db_session, plan.id, "Daily Activities", Decimal("10000.00"), Decimal("9200.00")
    )
    await db_session.commit()

    alerts = await svc.check_budget_alerts(db_session, plan.id)
    critical_alerts = [a for a in alerts if a.alert_type == "CRITICAL"]
    assert len(critical_alerts) == 1
    assert critical_alerts[0].severity == "critical"


async def test_overspent_alert_generated(db_session: AsyncSession):
    """An OVERSPENT alert is generated when spent > allocated."""
    participant, plan = await _make_plan(db_session)
    await _make_category(
        db_session, plan.id, "Daily Activities", Decimal("5000.00"), Decimal("5500.00")
    )
    await db_session.commit()

    alerts = await svc.check_budget_alerts(db_session, plan.id)
    overspent_alerts = [a for a in alerts if a.alert_type == "OVERSPENT"]
    assert len(overspent_alerts) == 1
    assert overspent_alerts[0].severity == "critical"


async def test_plan_expiring_alert_generated(db_session: AsyncSession):
    """A PLAN_EXPIRING alert is generated when plan ends in < 30 days."""
    participant, plan = await _make_plan(
        db_session,
        start=TODAY - timedelta(days=340),
        end=TODAY + timedelta(days=10),
    )
    await _make_category(db_session, plan.id)
    await db_session.commit()

    alerts = await svc.check_budget_alerts(db_session, plan.id)
    expiring_alerts = [a for a in alerts if a.alert_type == "PLAN_EXPIRING"]
    assert len(expiring_alerts) == 1
    assert expiring_alerts[0].severity == "warning"


async def test_recalculate_budget_from_invoices(db_session: AsyncSession):
    """recalculate_budget_spent sets budget_spent from approved invoice line items."""
    participant, plan = await _make_plan(db_session)
    cat = await _make_category(
        db_session, plan.id, "Daily Activities", Decimal("10000.00"), Decimal("0.00")
    )
    await _make_approved_invoice(
        db_session, participant.id, plan.id, cat.id, Decimal("1500.00")
    )
    await _make_approved_invoice(
        db_session, participant.id, plan.id, cat.id, Decimal("2500.00")
    )
    await db_session.commit()

    await svc.recalculate_budget_spent(db_session, plan.id)

    await db_session.refresh(cat)
    assert cat.budget_spent == Decimal("4000.00")


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


async def test_budget_summary_endpoint(test_client):
    """GET /budget/plans/{id}/summary returns 200 with correct structure."""
    p_resp = await test_client.post("/api/v1/participants/", json=make_participant_payload())
    assert p_resp.status_code == 201
    participant = p_resp.json()

    plan_resp = await test_client.post(
        "/api/v1/plans/",
        json={
            "participant_id": participant["id"],
            "plan_start_date": str(TODAY - timedelta(days=100)),
            "plan_end_date": str(TODAY + timedelta(days=265)),
            "total_funding": "50000.00",
        },
    )
    assert plan_resp.status_code == 201
    plan = plan_resp.json()

    resp = await test_client.get(f"/api/v1/budget/plans/{plan['id']}/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan_id"] == plan["id"]
    assert "total_allocated" in body
    assert "categories" in body
    assert "alerts" in body


async def test_budget_summary_not_found(test_client):
    """GET /budget/plans/{non-existent-id}/summary returns 404."""
    resp = await test_client.get(f"/api/v1/budget/plans/{uuid.uuid4()}/summary")
    assert resp.status_code == 404


async def test_recalculate_endpoint(test_client):
    """POST /budget/plans/{id}/recalculate returns 202."""
    p_resp = await test_client.post("/api/v1/participants/", json=make_participant_payload())
    participant = p_resp.json()

    plan_resp = await test_client.post(
        "/api/v1/plans/",
        json={
            "participant_id": participant["id"],
            "plan_start_date": str(TODAY - timedelta(days=50)),
            "plan_end_date": str(TODAY + timedelta(days=315)),
            "total_funding": "30000.00",
        },
    )
    plan = plan_resp.json()

    resp = await test_client.post(f"/api/v1/budget/plans/{plan['id']}/recalculate")
    assert resp.status_code == 202
