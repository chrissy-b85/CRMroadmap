"""FastAPI router for email correspondence history endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_db
from app.models.email_thread import EmailThread
from app.schemas.email_thread import EmailThreadOut

router = APIRouter(tags=["Correspondence"])


@router.get(
    "/participants/{participant_id}/correspondence",
    response_model=list[EmailThreadOut],
)
async def get_participant_correspondence(
    participant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get email correspondence history for a participant."""
    result = await db.execute(
        select(EmailThread)
        .where(EmailThread.participant_id == participant_id)
        .order_by(EmailThread.received_at.desc())
    )
    return result.scalars().all()


@router.get(
    "/providers/{provider_id}/correspondence",
    response_model=list[EmailThreadOut],
)
async def get_provider_correspondence(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get email correspondence history for a provider."""
    result = await db.execute(
        select(EmailThread)
        .where(EmailThread.provider_id == provider_id)
        .order_by(EmailThread.received_at.desc())
    )
    return result.scalars().all()
