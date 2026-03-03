"""Async service functions for SupportCategory CRUD and budget operations."""
import uuid
from decimal import Decimal
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.participant import Plan, SupportCategory
from app.schemas.support_category import (
    BudgetSummaryOut,
    SupportCategoryIn,
    SupportCategoryOut,
    SupportCategoryUpdate,
)


async def _get_plan_or_404(db: AsyncSession, plan_id: uuid.UUID) -> Plan:
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


async def _get_category_or_404(
    db: AsyncSession, category_id: uuid.UUID
) -> SupportCategory:
    result = await db.execute(
        select(SupportCategory).where(SupportCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support category not found",
        )
    return category


async def get_support_categories(
    db: AsyncSession, plan_id: uuid.UUID
) -> Sequence[SupportCategory]:
    """List all support categories for a plan; raise 404 if plan not found."""
    await _get_plan_or_404(db, plan_id)
    result = await db.execute(
        select(SupportCategory).where(SupportCategory.plan_id == plan_id)
    )
    return result.scalars().all()


async def get_support_category_by_id(
    db: AsyncSession, category_id: uuid.UUID
) -> SupportCategory:
    """Fetch a single support category; raise 404 if not found."""
    return await _get_category_or_404(db, category_id)


async def create_support_category(
    db: AsyncSession, plan_id: uuid.UUID, data: SupportCategoryIn
) -> SupportCategory:
    """Create a support category linked to a plan; raise 404 if plan not found."""
    await _get_plan_or_404(db, plan_id)
    category = SupportCategory(plan_id=plan_id, **data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def update_support_category(
    db: AsyncSession, category_id: uuid.UUID, data: SupportCategoryUpdate
) -> SupportCategory:
    """Partially update a support category; raise 404 if not found."""
    category = await _get_category_or_404(db, category_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    await db.commit()
    await db.refresh(category)
    return category


async def delete_support_category(
    db: AsyncSession, category_id: uuid.UUID
) -> None:
    """Hard-delete a support category; raise 404 if not found, 409 if it has spend."""
    category = await _get_category_or_404(db, category_id)
    if category.budget_spent and category.budget_spent > Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a support category with existing spend.",
        )
    await db.delete(category)
    await db.commit()


async def get_budget_summary(
    db: AsyncSession, plan_id: uuid.UUID
) -> BudgetSummaryOut:
    """Aggregate budget totals across all categories for a plan."""
    categories = await get_support_categories(db, plan_id)
    total_allocated = sum((c.budget_allocated for c in categories), Decimal("0.00"))
    total_spent = sum((c.budget_spent for c in categories), Decimal("0.00"))
    total_remaining = total_allocated - total_spent
    if total_allocated:
        overall_utilisation_percent = float(total_spent / total_allocated * 100)
    else:
        overall_utilisation_percent = 0.0
    return BudgetSummaryOut(
        plan_id=plan_id,
        total_allocated=total_allocated,
        total_spent=total_spent,
        total_remaining=total_remaining,
        overall_utilisation_percent=overall_utilisation_percent,
        categories=[SupportCategoryOut.model_validate(c) for c in categories],
    )


async def record_spend(
    db: AsyncSession, category_id: uuid.UUID, amount: Decimal
) -> SupportCategory:
    """Increment budget_spent by amount; raise 404 if category not found."""
    category = await _get_category_or_404(db, category_id)
    category.budget_spent = category.budget_spent + amount
    await db.commit()
    await db.refresh(category)
    return category


async def reverse_spend(
    db: AsyncSession, category_id: uuid.UUID, amount: Decimal
) -> SupportCategory:
    """Decrement budget_spent by amount; raise 404 if category not found."""
    category = await _get_category_or_404(db, category_id)
    category.budget_spent = category.budget_spent - amount
    await db.commit()
    await db.refresh(category)
    return category
