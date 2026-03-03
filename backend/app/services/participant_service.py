"""Async service functions for participant and plan CRUD operations."""

import uuid
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.participant import Participant, Plan
from app.schemas.participant import ParticipantIn, ParticipantUpdate
from app.schemas.plan import PlanIn


async def get_participants(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
) -> tuple[Sequence[Participant], int]:
    """Return a paginated list of participants with optional name/NDIS search."""
    query = select(Participant)
    count_query = select(func.count()).select_from(Participant)

    if search:
        like = f"%{search}%"
        condition = or_(
            Participant.first_name.ilike(like),
            Participant.last_name.ilike(like),
            Participant.ndis_number.ilike(like),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    items = result.scalars().all()

    return items, total


async def get_participant_by_id(
    db: AsyncSession, participant_id: uuid.UUID
) -> Participant:
    """Fetch a single participant; raise 404 if not found."""
    result = await db.execute(
        select(Participant).where(Participant.id == participant_id)
    )
    participant = result.scalar_one_or_none()
    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found"
        )
    return participant


async def create_participant(db: AsyncSession, data: ParticipantIn) -> Participant:
    """Create a new participant; raise 409 if the NDIS number already exists."""
    existing = await db.execute(
        select(Participant).where(Participant.ndis_number == data.ndis_number)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A participant with this NDIS number already exists",
        )
    participant = Participant(**data.model_dump())
    db.add(participant)
    await db.commit()
    await db.refresh(participant)
    return participant


async def update_participant(
    db: AsyncSession, participant_id: uuid.UUID, data: ParticipantUpdate
) -> Participant:
    """Partially update a participant's fields."""
    participant = await get_participant_by_id(db, participant_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(participant, field, value)
    await db.commit()
    await db.refresh(participant)
    return participant


async def deactivate_participant(db: AsyncSession, participant_id: uuid.UUID) -> None:
    """Soft-delete a participant by setting is_active=False."""
    participant = await get_participant_by_id(db, participant_id)
    participant.is_active = False
    await db.commit()


async def get_participant_plans(
    db: AsyncSession, participant_id: uuid.UUID
) -> Sequence[Plan]:
    """Return all plans linked to a participant (404 if participant missing)."""
    await get_participant_by_id(db, participant_id)
    result = await db.execute(select(Plan).where(Plan.participant_id == participant_id))
    return result.scalars().all()


async def create_participant_plan(
    db: AsyncSession, participant_id: uuid.UUID, data: PlanIn
) -> Plan:
    """Create a new NDIS plan linked to a participant."""
    await get_participant_by_id(db, participant_id)
    plan = Plan(participant_id=participant_id, **data.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan
