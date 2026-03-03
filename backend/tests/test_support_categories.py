"""Comprehensive tests for the /plans/{plan_id}/support-categories API."""
import uuid

import pytest
from httpx import AsyncClient

from tests.conftest import make_participant_payload

pytestmark = pytest.mark.asyncio

SAMPLE_PLAN_PAYLOAD = {
    "plan_start_date": "2024-07-01",
    "plan_end_date": "2025-06-30",
    "total_funding": "50000.00",
    "plan_manager": "Self-managed",
}

SAMPLE_CATEGORY_PAYLOAD = {
    "ndis_support_category": "Daily Activities",
    "ndis_support_number": "01",
    "budget_allocated": "10000.00",
}


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
    payload = dict(SAMPLE_PLAN_PAYLOAD)
    payload["participant_id"] = participant_id
    resp = await test_client.post("/api/v1/plans/", json=payload)
    assert resp.status_code == 201
    return resp.json()


async def _create_category(test_client: AsyncClient, plan_id: str, payload: dict | None = None) -> dict:
    data = payload or SAMPLE_CATEGORY_PAYLOAD
    resp = await test_client.post(
        f"/api/v1/plans/{plan_id}/support-categories", json=data
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_create_support_category_success(test_client: AsyncClient):
    """POST returns 201 with correct fields including computed fields."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])

    resp = await test_client.post(
        f"/api/v1/plans/{plan['id']}/support-categories",
        json=SAMPLE_CATEGORY_PAYLOAD,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["plan_id"] == plan["id"]
    assert body["ndis_support_category"] == "Daily Activities"
    assert body["ndis_support_number"] == "01"
    assert float(body["budget_allocated"]) == 10000.00
    assert float(body["budget_spent"]) == 0.00
    assert float(body["budget_remaining"]) == 10000.00
    assert body["utilisation_percent"] == 0.0
    assert body["is_overspent"] is False
    assert "id" in body


async def test_list_support_categories(test_client: AsyncClient):
    """GET returns all categories for a plan."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])

    await _create_category(test_client, plan["id"])
    await _create_category(
        test_client,
        plan["id"],
        {"ndis_support_category": "Transport", "ndis_support_number": "02", "budget_allocated": "5000.00"},
    )

    resp = await test_client.get(f"/api/v1/plans/{plan['id']}/support-categories")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 2
    assert all(item["plan_id"] == plan["id"] for item in body)


async def test_get_budget_summary(test_client: AsyncClient):
    """GET /summary returns correct aggregated totals and utilisation."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])

    await _create_category(test_client, plan["id"], {"ndis_support_category": "Daily Activities", "budget_allocated": "10000.00"})
    await _create_category(test_client, plan["id"], {"ndis_support_category": "Transport", "budget_allocated": "4000.00"})

    resp = await test_client.get(f"/api/v1/plans/{plan['id']}/support-categories/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan_id"] == plan["id"]
    assert float(body["total_allocated"]) == 14000.00
    assert float(body["total_spent"]) == 0.00
    assert float(body["total_remaining"]) == 14000.00
    assert body["overall_utilisation_percent"] == 0.0
    assert isinstance(body["categories"], list)
    assert len(body["categories"]) == 2


async def test_update_budget_allocation(test_client: AsyncClient):
    """PATCH updates budget_allocated and recalculates computed fields."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])
    category = await _create_category(test_client, plan["id"])

    resp = await test_client.patch(
        f"/api/v1/plans/{plan['id']}/support-categories/{category['id']}",
        json={"budget_allocated": "15000.00"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert float(body["budget_allocated"]) == 15000.00
    assert float(body["budget_remaining"]) == 15000.00


async def test_record_spend_updates_budget(test_client: AsyncClient):
    """POST /{id}/record-spend increments budget_spent and updates budget_remaining."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])
    category = await _create_category(test_client, plan["id"])

    resp = await test_client.post(
        f"/api/v1/plans/{plan['id']}/support-categories/{category['id']}/record-spend",
        params={"amount": "2500.00"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert float(body["budget_spent"]) == 2500.00
    assert float(body["budget_remaining"]) == 7500.00
    assert body["is_overspent"] is False


async def test_overspend_flagged(test_client: AsyncClient):
    """is_overspent=True when budget_spent exceeds budget_allocated."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])
    category = await _create_category(test_client, plan["id"])

    resp = await test_client.post(
        f"/api/v1/plans/{plan['id']}/support-categories/{category['id']}/record-spend",
        params={"amount": "12000.00"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert float(body["budget_spent"]) == 12000.00
    assert body["is_overspent"] is True
    assert float(body["budget_remaining"]) == -2000.00


async def test_reverse_spend(test_client: AsyncClient):
    """Reversing spend decrements budget_spent correctly."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])
    category = await _create_category(test_client, plan["id"])

    # First record some spend
    await test_client.post(
        f"/api/v1/plans/{plan['id']}/support-categories/{category['id']}/record-spend",
        params={"amount": "3000.00"},
    )

    # Reverse part of the spend via PATCH
    resp = await test_client.patch(
        f"/api/v1/plans/{plan['id']}/support-categories/{category['id']}",
        json={"budget_spent": "1000.00"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert float(body["budget_spent"]) == 1000.00
    assert float(body["budget_remaining"]) == 9000.00


async def test_delete_support_category_no_spend(test_client: AsyncClient):
    """DELETE returns 204 when the category has zero spend."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])
    category = await _create_category(test_client, plan["id"])

    resp = await test_client.delete(
        f"/api/v1/plans/{plan['id']}/support-categories/{category['id']}"
    )
    assert resp.status_code == 204

    # Confirm it's gone
    get_resp = await test_client.get(
        f"/api/v1/plans/{plan['id']}/support-categories/{category['id']}"
    )
    assert get_resp.status_code == 404


async def test_delete_support_category_with_spend_rejected(test_client: AsyncClient):
    """DELETE returns 409 when the category has existing spend."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])
    category = await _create_category(test_client, plan["id"])

    # Record some spend first
    await test_client.post(
        f"/api/v1/plans/{plan['id']}/support-categories/{category['id']}/record-spend",
        params={"amount": "500.00"},
    )

    resp = await test_client.delete(
        f"/api/v1/plans/{plan['id']}/support-categories/{category['id']}"
    )
    assert resp.status_code == 409


async def test_get_support_category_not_found(test_client: AsyncClient):
    """GET /{category_id} returns 404 for a non-existent category."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])
    fake_id = str(uuid.uuid4())

    resp = await test_client.get(
        f"/api/v1/plans/{plan['id']}/support-categories/{fake_id}"
    )
    assert resp.status_code == 404
