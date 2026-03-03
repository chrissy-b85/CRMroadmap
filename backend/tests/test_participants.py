"""Comprehensive test suite for the /participants API endpoints."""

import pytest
from httpx import AsyncClient

from tests.conftest import SAMPLE_PLAN_PAYLOAD, make_participant_payload

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Listing participants
# ---------------------------------------------------------------------------


async def test_list_participants_empty(test_client: AsyncClient):
    """GET /participants/ on a fresh DB returns an empty list."""
    resp = await test_client.get("/api/v1/participants/")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert isinstance(body["items"], list)


async def test_list_participants_pagination(test_client: AsyncClient):
    """page/page_size query params are reflected in the response."""
    # Create two participants first
    for _ in range(2):
        await test_client.post("/api/v1/participants/", json=make_participant_payload())

    resp = await test_client.get("/api/v1/participants/?page=1&page_size=1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert len(body["items"]) <= 1


async def test_list_participants_search(test_client: AsyncClient):
    """search param filters by name or NDIS number."""
    unique_name = "Zephyrine"
    payload = make_participant_payload()
    payload["first_name"] = unique_name
    create_resp = await test_client.post("/api/v1/participants/", json=payload)
    assert create_resp.status_code == 201

    resp = await test_client.get(f"/api/v1/participants/?search={unique_name}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert any(p["first_name"] == unique_name for p in body["items"])


# ---------------------------------------------------------------------------
# Creating participants
# ---------------------------------------------------------------------------


async def test_create_participant_success(test_client: AsyncClient):
    """POST /participants/ returns 201 with the correct response body."""
    payload = make_participant_payload()
    resp = await test_client.post("/api/v1/participants/", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["ndis_number"] == payload["ndis_number"]
    assert body["first_name"] == payload["first_name"]
    assert "id" in body
    assert body["is_active"] is True


async def test_create_participant_duplicate_ndis(test_client: AsyncClient):
    """POST /participants/ with duplicate NDIS number returns 409."""
    payload = make_participant_payload()
    first = await test_client.post("/api/v1/participants/", json=payload)
    assert first.status_code == 201

    second = await test_client.post("/api/v1/participants/", json=payload)
    assert second.status_code == 409


async def test_create_participant_invalid_data(test_client: AsyncClient):
    """POST /participants/ with missing required fields returns 422."""
    resp = await test_client.post(
        "/api/v1/participants/", json={"first_name": "No NDIS"}
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Getting a single participant
# ---------------------------------------------------------------------------


async def test_get_participant_success(
    test_client: AsyncClient, sample_participant: dict
):
    """GET /participants/{id} returns 200 with the correct participant."""
    pid = sample_participant["id"]
    resp = await test_client.get(f"/api/v1/participants/{pid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == pid
    assert body["ndis_number"] == sample_participant["ndis_number"]


async def test_get_participant_not_found(test_client: AsyncClient):
    """GET /participants/{non-existent-id} returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await test_client.get(f"/api/v1/participants/{fake_id}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Updating a participant
# ---------------------------------------------------------------------------


async def test_update_participant_success(
    test_client: AsyncClient, sample_participant: dict
):
    """PATCH /participants/{id} updates specified fields and returns 200."""
    pid = sample_participant["id"]
    resp = await test_client.patch(
        f"/api/v1/participants/{pid}", json={"first_name": "Updated"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["first_name"] == "Updated"
    assert body["last_name"] == sample_participant["last_name"]


# ---------------------------------------------------------------------------
# Deactivating a participant
# ---------------------------------------------------------------------------


async def test_deactivate_participant_success(
    test_client: AsyncClient, sample_participant: dict
):
    """DELETE /participants/{id} returns 204 and the participant is deactivated."""
    pid = sample_participant["id"]
    resp = await test_client.delete(f"/api/v1/participants/{pid}")
    assert resp.status_code == 204

    # Verify is_active is now False
    get_resp = await test_client.get(f"/api/v1/participants/{pid}")
    assert get_resp.status_code == 200
    assert get_resp.json()["is_active"] is False


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------


async def test_create_plan_for_participant(
    test_client: AsyncClient, sample_participant: dict
):
    """POST /participants/{id}/plans returns 201 linked to the participant."""
    pid = sample_participant["id"]
    resp = await test_client.post(
        f"/api/v1/participants/{pid}/plans", json=SAMPLE_PLAN_PAYLOAD
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["participant_id"] == pid
    assert "id" in body


async def test_list_plans_for_participant(
    test_client: AsyncClient, sample_participant: dict
):
    """GET /participants/{id}/plans returns the plans linked to that participant."""
    pid = sample_participant["id"]
    # Create a plan first
    await test_client.post(
        f"/api/v1/participants/{pid}/plans", json=SAMPLE_PLAN_PAYLOAD
    )

    resp = await test_client.get(f"/api/v1/participants/{pid}/plans")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert all(p["participant_id"] == pid for p in body)
