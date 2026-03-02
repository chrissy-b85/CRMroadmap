"""FastAPI router for participant management endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_role
from app.db import get_db
from app.schemas.participant import (
    ParticipantIn,
    ParticipantListOut,
    ParticipantOut,
    ParticipantUpdate,
)
from app.schemas.plan import PlanIn, PlanOut
from app.services import participant_service as svc

router = APIRouter(prefix="/participants", tags=["Participants"])


@router.get("/", response_model=ParticipantListOut)
async def list_participants(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all participants with pagination and optional search."""
    items, total = await svc.get_participants(db, page, page_size, search)
    return ParticipantListOut(
        items=items, total=total, page=page, page_size=page_size
    )


@router.post("/", response_model=ParticipantOut, status_code=status.HTTP_201_CREATED)
async def create_participant(
    data: ParticipantIn,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Create a new participant. Requires Coordinator or Admin role."""
    return await svc.create_participant(db, data)


@router.get("/{participant_id}", response_model=ParticipantOut)
async def get_participant(
    participant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single participant by ID."""
    return await svc.get_participant_by_id(db, participant_id)


@router.patch("/{participant_id}", response_model=ParticipantOut)
async def update_participant(
    participant_id: UUID,
    data: ParticipantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Update participant details. Requires Coordinator or Admin role."""
    return await svc.update_participant(db, participant_id, data)


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_participant(
    participant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Admin")),
):
    """Deactivate a participant (soft delete). Requires Admin role."""
    await svc.deactivate_participant(db, participant_id)


@router.get("/{participant_id}/plans", response_model=list[PlanOut])
async def list_plans(
    participant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all NDIS plans for a participant."""
    return await svc.get_participant_plans(db, participant_id)


@router.post(
    "/{participant_id}/plans",
    response_model=PlanOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_plan(
    participant_id: UUID,
    data: PlanIn,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Create and link a new NDIS plan to a participant. Requires Coordinator or Admin role."""
    return await svc.create_participant_plan(db, participant_id, data)
