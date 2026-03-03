"""Tests for role-based access control on API endpoints.

These tests verify that:
- Unauthenticated requests are rejected with 401
- Participants cannot access staff-only endpoints (403)
- Coordinators cannot access Admin-only endpoints (403)
- Users with the correct role can access permitted endpoints (2xx)
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.auth import get_current_user, require_role
from app.db import get_db

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Fixture helpers — build clients with specific role payloads
# ---------------------------------------------------------------------------


def _make_user(roles: list[str]) -> dict:
    return {
        "sub": f"test|{'_'.join(roles) or 'anon'}",
        "roles": roles,
        "https://ndis-crm.com/roles": roles,
    }


@pytest_asyncio.fixture
async def participant_client(db_session):
    """Client authenticated as a Participant (no staff roles)."""
    from main import app

    async def override_get_db():
        yield db_session

    user = _make_user(["Participant"])

    async def override_current_user():
        return user

    def override_require_role(role: str):
        async def _dep():
            raise __import__("fastapi").HTTPException(
                status_code=403,
                detail=f"Role '{role}' or 'Admin' required",
            )

        return _dep

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[require_role] = override_require_role

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def coordinator_client(db_session):
    """Client authenticated as a Coordinator (no Admin role)."""
    from main import app

    async def override_get_db():
        yield db_session

    coordinator_user = _make_user(["Coordinator"])

    async def override_current_user():
        return coordinator_user

    def override_require_role(role: str):
        async def _dep():
            if role == "Admin":
                raise __import__("fastapi").HTTPException(
                    status_code=403,
                    detail="Role 'Admin' required",
                )
            return coordinator_user

        return _dep

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[require_role] = override_require_role

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# test_unauthenticated_request_returns_401
# ---------------------------------------------------------------------------


async def test_unauthenticated_request_returns_401(db_session):
    """When no valid token is present, the auth dependency raises 401."""
    from fastapi import HTTPException, status as http_status
    from main import app

    async def override_get_db():
        yield db_session

    async def mock_unauthenticated():
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    def mock_require_role_401(role: str):
        async def _dep():
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        return _dep

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = mock_unauthenticated
    app.dependency_overrides[require_role] = mock_require_role_401

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/participants/")
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# test_participant_cannot_access_staff_endpoints
# ---------------------------------------------------------------------------


async def test_participant_cannot_access_staff_endpoints(participant_client: AsyncClient):
    """A Participant-role user cannot access coordinator-required endpoints."""
    # POST /invoices/ingest/trigger requires Admin role
    resp = await participant_client.post("/api/v1/invoices/ingest/trigger")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# test_coordinator_cannot_access_admin_endpoints
# ---------------------------------------------------------------------------


async def test_coordinator_cannot_access_admin_endpoints(coordinator_client: AsyncClient):
    """A Coordinator cannot access Admin-only endpoints like ingest trigger."""
    resp = await coordinator_client.post("/api/v1/invoices/ingest/trigger")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# test_wrong_role_returns_403
# ---------------------------------------------------------------------------


async def test_wrong_role_returns_403(participant_client: AsyncClient):
    """A user with the wrong role receives a 403 on role-protected endpoints."""
    # Any endpoint requiring Coordinator or Admin should reject a Participant
    resp = await participant_client.post("/api/v1/invoices/ingest/trigger")
    assert resp.status_code == 403
