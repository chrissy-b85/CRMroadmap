"""FastAPI router for support category endpoints nested under plans."""
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_role
from app.db import get_db
from app.schemas.support_category import (
    BudgetSummaryOut,
    SupportCategoryIn,
    SupportCategoryOut,
    SupportCategoryUpdate,
)
from app.services import support_category_service as svc

router = APIRouter(
    prefix="/plans/{plan_id}/support-categories",
    tags=["Support Categories"],
)


@router.get("", response_model=list[SupportCategoryOut])
async def list_support_categories(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all support categories for a plan with budget status."""
    return await svc.get_support_categories(db, plan_id)


@router.post("", response_model=SupportCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_support_category(
    plan_id: UUID,
    data: SupportCategoryIn,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Add a support category with budget allocation to a plan."""
    return await svc.create_support_category(db, plan_id, data)


@router.get("/summary", response_model=BudgetSummaryOut)
async def get_budget_summary(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get aggregated budget summary across all categories for a plan."""
    return await svc.get_budget_summary(db, plan_id)


@router.get("/{category_id}", response_model=SupportCategoryOut)
async def get_support_category(
    plan_id: UUID,
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single support category by ID."""
    return await svc.get_support_category_by_id(db, category_id, plan_id)


@router.patch("/{category_id}", response_model=SupportCategoryOut)
async def update_support_category(
    plan_id: UUID,
    category_id: UUID,
    data: SupportCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Update support category budget allocation."""
    return await svc.update_support_category(db, category_id, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_support_category(
    plan_id: UUID,
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Admin")),
):
    """Delete a support category (Admin only, no existing spend)."""
    await svc.delete_support_category(db, category_id)


@router.post("/{category_id}/record-spend", response_model=SupportCategoryOut)
async def record_spend(
    plan_id: UUID,
    category_id: UUID,
    amount: Decimal = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Record spend against a support category (called when invoice approved)."""
    return await svc.record_spend(db, category_id, amount)
