"""FastAPI router for Xero OAuth2 connect/disconnect flow."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_role
from app.db import get_db
from app.integrations.xero.client import XeroClient
from app.models.xero_connection import XeroConnection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/xero", tags=["Xero"])

# In-memory state store (sufficient for single-instance deployments; use Redis
# for multi-instance).
_pending_states: dict[str, bool] = {}


@router.get("/connect")
async def xero_connect(
    current_user: dict = Depends(require_role("Admin")),
):
    """Initiate Xero OAuth2 connection (Admin only).

    Returns a redirect URL the client should navigate to.
    """
    client = XeroClient()
    auth_url, state = await client.get_auth_url()
    _pending_states[state] = True
    return {"auth_url": auth_url, "state": state}


@router.get("/callback")
async def xero_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle Xero OAuth2 callback, exchange code for tokens and store them."""
    if state not in _pending_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state",
        )
    del _pending_states[state]

    client = XeroClient()
    try:
        tokens = await client.exchange_code(code)
        tenant_id = await client.get_tenant_id()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Xero token exchange failed: {exc}",
        ) from exc

    # Deactivate any existing connections
    existing = await db.execute(
        select(XeroConnection).where(XeroConnection.is_active.is_(True))
    )
    for conn in existing.scalars().all():
        conn.is_active = False

    expiry = datetime.now(tz=timezone.utc) + timedelta(seconds=tokens.expires_in)
    new_conn = XeroConnection(
        tenant_id=tenant_id,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_expiry=expiry,
        is_active=True,
    )
    db.add(new_conn)
    await db.commit()

    logger.info("Xero connection established for tenant %s", tenant_id)
    return {"detail": "Xero connected", "tenant_id": tenant_id}


@router.delete("/disconnect")
async def xero_disconnect(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Admin")),
):
    """Disconnect Xero integration (Admin only)."""
    result = await db.execute(
        select(XeroConnection).where(XeroConnection.is_active.is_(True))
    )
    connections = result.scalars().all()
    if not connections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Xero connection",
        )
    for conn in connections:
        conn.is_active = False
    await db.commit()
    logger.info("Xero connection deactivated")
    return {"detail": "Xero disconnected"}


@router.get("/status")
async def xero_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get Xero connection status."""
    result = await db.execute(
        select(XeroConnection)
        .where(XeroConnection.is_active.is_(True))
        .order_by(XeroConnection.created_at.desc())
        .limit(1)
    )
    conn = result.scalar_one_or_none()
    if conn is None:
        return {"connected": False}
    return {
        "connected": True,
        "tenant_id": conn.tenant_id,
        "token_expiry": conn.token_expiry.isoformat(),
    }
