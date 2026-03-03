"""FastAPI dependency for participant-scoped authentication."""

from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db import get_db


async def get_current_participant(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the Participant record for the currently authenticated user.

    Looks up the participant by matching their Auth0 ``sub`` claim against the
    ``auth0_sub`` column on the Participant table.

    Raises:
        HTTPException 403: if no participant profile exists for this user.
    """
    from app.models.participant import Participant

    sub = current_user.get("sub", "")
    result = await db.execute(
        select(Participant).where(Participant.auth0_sub == sub)
    )
    participant = result.scalar_one_or_none()
    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No participant profile found for this user.",
        )
    return participant
