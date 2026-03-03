"""Comprehensive test suite for the /plans API endpoints."""
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

SAMPLE_SUPPORT_CATEGORY_PAYLOAD = {
    "ndis_support_category": "Daily Activities",
    "budget_allocated": "10000.00",
}


# ---------------------------------------------------------------------------
# Helper
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


# ---------------------------------------------------------------------------
# List plans
# ---------------------------------------------------------------------------


async def test_list_plans_empty(test_client: AsyncClient):
    """GET /plans/ returns an empty list when no active plans exist."""
    resp = await test_client.get("/api/v1/plans/?active_only=false")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert isinstance(body["items"], list)


async def test_list_plans_filter_by_participant(test_client: AsyncClient):
    """GET /plans/?participant_id= filters correctly."""
    p1 = await _create_participant(test_client)
    p2 = await _create_participant(test_client)
    plan1 = await _create_plan(test_client, p1["id"])
    await _create_plan(test_client, p2["id"])

    resp = await test_client.get(
        f"/api/v1/plans/?participant_id={p1['id']}&active_only=false"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert all(item["participant_id"] == p1["id"] for item in body["items"])
    plan_ids = [item["id"] for item in body["items"]]
    assert plan1["id"] in plan_ids


# ---------------------------------------------------------------------------
# Create plan
# ---------------------------------------------------------------------------


async def test_create_plan_success(test_client: AsyncClient):
    """POST /plans/ returns 201 with correct response body."""
    participant = await _create_participant(test_client)
    payload = dict(SAMPLE_PLAN_PAYLOAD)
    payload["participant_id"] = participant["id"]

    resp = await test_client.post("/api/v1/plans/", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["participant_id"] == participant["id"]
    assert body["plan_manager"] == "Self-managed"
    assert body["is_active"] is True
    assert "id" in body
    assert "support_categories" in body
    assert isinstance(body["support_categories"], list)


async def test_create_plan_invalid_dates(test_client: AsyncClient):
    """POST /plans/ with end_date <= start_date returns 422."""
    participant = await _create_participant(test_client)
    payload = {
        "participant_id": participant["id"],
        "plan_start_date": "2025-06-30",
        "plan_end_date": "2024-07-01",
        "total_funding": "50000.00",
    }
    resp = await test_client.post("/api/v1/plans/", json=payload)
    assert resp.status_code == 422


async def test_create_plan_participant_not_found(test_client: AsyncClient):
    """POST /plans/ with non-existent participant returns 404."""
    payload = dict(SAMPLE_PLAN_PAYLOAD)
    payload["participant_id"] = str(uuid.uuid4())

    resp = await test_client.post("/api/v1/plans/", json=payload)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Get plan
# ---------------------------------------------------------------------------


async def test_get_plan_success(test_client: AsyncClient):
    """GET /plans/{id} returns 200 with correct data including support categories."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])

    resp = await test_client.get(f"/api/v1/plans/{plan['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == plan["id"]
    assert body["participant_id"] == participant["id"]
    assert "support_categories" in body
    assert isinstance(body["support_categories"], list)


async def test_get_plan_not_found(test_client: AsyncClient):
    """GET /plans/{non-existent-id} returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await test_client.get(f"/api/v1/plans/{fake_id}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update plan
# ---------------------------------------------------------------------------


async def test_update_plan_success(test_client: AsyncClient):
    """PATCH /plans/{id} updates fields and returns 200."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])

    resp = await test_client.patch(
        f"/api/v1/plans/{plan['id']}", json={"plan_manager": "Agency-managed"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan_manager"] == "Agency-managed"
    assert body["id"] == plan["id"]


async def test_update_plan_invalid_dates(test_client: AsyncClient):
    """PATCH /plans/{id} with end_date <= start_date returns 422."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])

    resp = await test_client.patch(
        f"/api/v1/plans/{plan['id']}",
        json={"plan_start_date": "2025-01-01", "plan_end_date": "2024-01-01"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Deactivate plan
# ---------------------------------------------------------------------------


async def test_deactivate_plan_success(test_client: AsyncClient):
    """DELETE /plans/{id} returns 204 and plan is deactivated."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])

    resp = await test_client.delete(f"/api/v1/plans/{plan['id']}")
    assert resp.status_code == 204

    get_resp = await test_client.get(f"/api/v1/plans/{plan['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["is_active"] is False


# ---------------------------------------------------------------------------
# Support categories
# ---------------------------------------------------------------------------


async def test_create_support_category_success(test_client: AsyncClient):
    """POST /plans/{id}/support-categories returns 201 linked to plan."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])

    resp = await test_client.post(
        f"/api/v1/plans/{plan['id']}/support-categories",
        json=SAMPLE_SUPPORT_CATEGORY_PAYLOAD,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["plan_id"] == plan["id"]
    assert body["ndis_support_category"] == "Daily Activities"
    assert "budget_remaining" in body
    assert "budget_spent" in body


async def test_list_support_categories(test_client: AsyncClient):
    """GET /plans/{id}/support-categories returns correct categories."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])

    await test_client.post(
        f"/api/v1/plans/{plan['id']}/support-categories",
        json=SAMPLE_SUPPORT_CATEGORY_PAYLOAD,
    )

    resp = await test_client.get(f"/api/v1/plans/{plan['id']}/support-categories")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert all(item["plan_id"] == plan["id"] for item in body)


async def test_update_support_category_budget(test_client: AsyncClient):
    """PATCH /plans/{id}/support-categories/{cat_id} updates budget_spent correctly."""
    participant = await _create_participant(test_client)
    plan = await _create_plan(test_client, participant["id"])

    cat_resp = await test_client.post(
        f"/api/v1/plans/{plan['id']}/support-categories",
        json=SAMPLE_SUPPORT_CATEGORY_PAYLOAD,
    )
    assert cat_resp.status_code == 201
    category = cat_resp.json()

    resp = await test_client.patch(
        f"/api/v1/plans/{plan['id']}/support-categories/{category['id']}",
        json={"budget_spent": "2500.00"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert float(body["budget_spent"]) == 2500.00
    assert float(body["budget_remaining"]) == float(body["budget_allocated"]) - 2500.00
