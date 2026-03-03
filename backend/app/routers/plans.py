"""FastAPI router for plan management endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_role
from app.db import get_db
from app.schemas.plan import PlanIn, PlanListOut, PlanOut, PlanUpdate
from app.services import plan_service as svc

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("/", response_model=PlanListOut)
async def list_plans(
    page: int = 1,
    page_size: int = 20,
    participant_id: UUID | None = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all plans with optional filtering by participant."""
    items, total = await svc.get_plans(db, page, page_size, participant_id, active_only)
    return PlanListOut(items=items, total=total, page=page, page_size=page_size)


@router.post("/", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: PlanIn,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Create a new NDIS plan linked to a participant. Requires Coordinator or Admin role."""
    return await svc.create_plan(db, data)


@router.get("/{plan_id}", response_model=PlanOut)
async def get_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single plan by ID, including support categories."""
    return await svc.get_plan_by_id(db, plan_id)


@router.patch("/{plan_id}", response_model=PlanOut)
async def update_plan(
    plan_id: UUID,
    data: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Update plan details. Requires Coordinator or Admin role."""
    return await svc.update_plan(db, plan_id, data)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Admin")),
):
    """Deactivate a plan (soft delete). Requires Admin role."""
    await svc.deactivate_plan(db, plan_id)
