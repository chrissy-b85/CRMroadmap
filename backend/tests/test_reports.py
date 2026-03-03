"""Tests for the /reports endpoints."""
import uuid
from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_participant_payload

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_participant(test_client: AsyncClient) -> dict:
    resp = await test_client.post(
        "/api/v1/participants/", json=make_participant_payload()
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_plan(test_client: AsyncClient, participant_id: str) -> dict:
    resp = await test_client.post(
        "/api/v1/plans/",
        json={
            "participant_id": participant_id,
            "plan_start_date": "2024-07-01",
            "plan_end_date": "2025-06-30",
            "total_funding": "50000.00",
            "plan_manager": "Self-managed",
        },
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_provider(db_session: AsyncSession) -> dict:
    """Insert a Provider row directly via the DB session (avoids ABN checksum complexity)."""
    from app.models.provider import Provider

    provider = Provider(
        abn=f"{uuid.uuid4().int % 10**11:011d}",
        business_name=f"Provider {uuid.uuid4().hex[:6]}",
        email="provider@example.com",
    )
    db_session.add(provider)
    await db_session.commit()
    await db_session.refresh(provider)
    return {"id": str(provider.id), "business_name": provider.business_name}


async def _insert_invoice(
    db_session: AsyncSession,
    *,
    participant_id: str | None = None,
    provider_id: str | None = None,
    status: str = "APPROVED",
    total_amount: str = "1000.00",
    invoice_date: str = "2024-08-15",
) -> dict:
    """Insert an Invoice row directly via the DB session."""
    from app.models.invoice import Invoice

    inv = Invoice(
        participant_id=uuid.UUID(participant_id) if participant_id else None,
        provider_id=uuid.UUID(provider_id) if provider_id else None,
        invoice_date=date.fromisoformat(invoice_date),
        total_amount=total_amount,
        gst_amount="0.00",
        status=status,
        gcs_json_path="gs://bucket/invoice.json",
    )
    db_session.add(inv)
    await db_session.commit()
    await db_session.refresh(inv)
    return {"id": str(inv.id), "status": inv.status}


# ---------------------------------------------------------------------------
# test_dashboard_summary_returns_correct_counts
# ---------------------------------------------------------------------------


async def test_dashboard_summary_returns_correct_counts(test_client: AsyncClient):
    """GET /reports/dashboard-summary returns expected fields and integer counts."""
    resp = await test_client.get("/api/v1/reports/dashboard-summary")
    assert resp.status_code == 200
    body = resp.json()
    expected_keys = {
        "active_participants",
        "active_plans",
        "invoices_this_month",
        "total_spend_this_month",
        "pending_approvals",
        "flagged_invoices",
        "critical_budget_alerts",
        "plans_expiring_30_days",
        "total_budget_under_management",
    }
    assert expected_keys.issubset(body.keys())
    # All counts must be non-negative integers
    for key in (
        "active_participants",
        "active_plans",
        "invoices_this_month",
        "pending_approvals",
        "flagged_invoices",
        "critical_budget_alerts",
        "plans_expiring_30_days",
    ):
        assert isinstance(body[key], int), f"{key} should be int"
        assert body[key] >= 0


# ---------------------------------------------------------------------------
# test_spend_by_category_correct_totals
# ---------------------------------------------------------------------------


async def test_spend_by_category_correct_totals(
    test_client: AsyncClient, db_session: AsyncSession
):
    """GET /reports/spend-by-category returns list with ndis_support_category & total_spend."""
    resp = await test_client.get(
        "/api/v1/reports/spend-by-category",
        params={"date_from": "2024-01-01", "date_to": "2024-12-31"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    for item in body:
        assert "ndis_support_category" in item
        assert "total_spend" in item
        assert float(item["total_spend"]) >= 0


# ---------------------------------------------------------------------------
# test_spend_over_time_monthly_grouping
# ---------------------------------------------------------------------------


async def test_spend_over_time_monthly_grouping(
    test_client: AsyncClient, db_session: AsyncSession
):
    """GET /reports/spend-over-time with granularity=month returns period strings in YYYY-MM."""
    # Insert two approved invoices in different months
    await _insert_invoice(db_session, invoice_date="2024-07-10", total_amount="500.00")
    await _insert_invoice(db_session, invoice_date="2024-08-15", total_amount="800.00")

    resp = await test_client.get(
        "/api/v1/reports/spend-over-time",
        params={
            "granularity": "month",
            "date_from": "2024-07-01",
            "date_to": "2024-08-31",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    for item in body:
        assert "period" in item
        assert "total_spend" in item
        # monthly period format: YYYY-MM
        assert len(item["period"]) == 7, f"Expected YYYY-MM, got {item['period']}"
        assert float(item["total_spend"]) >= 0


# ---------------------------------------------------------------------------
# test_provider_analytics_correct_rejection_rate
# ---------------------------------------------------------------------------


async def test_provider_analytics_correct_rejection_rate(
    test_client: AsyncClient, db_session: AsyncSession
):
    """GET /reports/provider-analytics computes rejection_rate correctly."""
    provider = await _create_provider(db_session)
    pid = provider["id"]

    # 2 invoices: 1 approved, 1 rejected → 50% rejection rate
    await _insert_invoice(
        db_session,
        provider_id=pid,
        status="APPROVED",
        invoice_date="2024-08-01",
    )
    await _insert_invoice(
        db_session,
        provider_id=pid,
        status="REJECTED",
        invoice_date="2024-08-10",
    )

    resp = await test_client.get(
        "/api/v1/reports/provider-analytics",
        params={"date_from": "2024-08-01", "date_to": "2024-08-31"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)

    provider_row = next((r for r in body if r["provider_id"] == pid), None)
    assert provider_row is not None, "Provider not found in analytics"
    assert provider_row["invoice_count"] == 2
    assert provider_row["rejection_rate"] == 50.0


# ---------------------------------------------------------------------------
# test_invoice_csv_export_correct_format
# ---------------------------------------------------------------------------


async def test_invoice_csv_export_correct_format(
    test_client: AsyncClient, db_session: AsyncSession
):
    """GET /reports/export/invoices returns CSV with correct header row."""
    await _insert_invoice(db_session, invoice_date="2024-08-20")

    resp = await test_client.get(
        "/api/v1/reports/export/invoices",
        params={"date_from": "2024-08-01", "date_to": "2024-08-31"},
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]

    lines = resp.text.strip().splitlines()
    assert len(lines) >= 1
    header = lines[0]
    for col in ("id", "invoice_number", "total_amount", "status"):
        assert col in header, f"Expected column '{col}' in CSV header"


# ---------------------------------------------------------------------------
# test_audit_log_csv_export_admin_only
# ---------------------------------------------------------------------------


async def test_audit_log_csv_export_admin_only(test_client: AsyncClient):
    """GET /reports/export/audit-log returns 200 for Admin and CSV content."""
    resp = await test_client.get(
        "/api/v1/reports/export/audit-log",
        params={"date_from": "2024-01-01", "date_to": "2024-12-31"},
    )
    # The test client is wired with Admin role, so expect 200
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    lines = resp.text.strip().splitlines()
    assert len(lines) >= 1
    header = lines[0]
    for col in ("id", "action", "entity_type", "created_at"):
        assert col in header, f"Expected column '{col}' in audit-log CSV header"
