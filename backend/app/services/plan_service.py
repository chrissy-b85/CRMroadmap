"""Async service functions for Plan and SupportCategory CRUD operations."""
import uuid
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.participant import Participant, Plan, SupportCategory
from app.schemas.plan import PlanIn, PlanUpdate
from app.schemas.support_category import SupportCategoryIn, SupportCategoryUpdate


async def get_plans(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    participant_id: uuid.UUID | None = None,
    active_only: bool = True,
) -> tuple[Sequence[Plan], int]:
    """Return a paginated list of plans, optionally filtered by participant."""
    query = select(Plan).options(selectinload(Plan.support_categories))
    count_query = select(func.count()).select_from(Plan)

    if participant_id is not None:
        query = query.where(Plan.participant_id == participant_id)
        count_query = count_query.where(Plan.participant_id == participant_id)

    if active_only:
        query = query.where(Plan.is_active.is_(True))
        count_query = count_query.where(Plan.is_active.is_(True))

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    items = result.scalars().all()

    return items, total


async def get_plan_by_id(db: AsyncSession, plan_id: uuid.UUID) -> Plan:
    """Fetch a single plan with support categories; raise 404 if not found."""
    result = await db.execute(
        select(Plan)
        .options(selectinload(Plan.support_categories))
        .where(Plan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )
    return plan


async def create_plan(db: AsyncSession, data: PlanIn) -> Plan:
    """Create a new plan; raise 404 if the participant does not exist."""
    participant = await db.execute(
        select(Participant).where(Participant.id == data.participant_id)
    )
    if participant.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found"
        )
    plan = Plan(**data.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    # Load support_categories relationship
    result = await db.execute(
        select(Plan)
        .options(selectinload(Plan.support_categories))
        .where(Plan.id == plan.id)
    )
    return result.scalar_one()


async def update_plan(
    db: AsyncSession, plan_id: uuid.UUID, data: PlanUpdate
) -> Plan:
    """Partially update a plan's fields."""
    plan = await get_plan_by_id(db, plan_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    await db.commit()
    await db.refresh(plan)
    result = await db.execute(
        select(Plan)
        .options(selectinload(Plan.support_categories))
        .where(Plan.id == plan_id)
    )
    return result.scalar_one()


async def deactivate_plan(db: AsyncSession, plan_id: uuid.UUID) -> None:
    """Soft-delete a plan by setting is_active=False."""
    plan = await get_plan_by_id(db, plan_id)
    plan.is_active = False
    await db.commit()


async def get_plan_support_categories(
    db: AsyncSession, plan_id: uuid.UUID
) -> Sequence[SupportCategory]:
    """Return all support categories for a plan; raise 404 if plan not found."""
    await get_plan_by_id(db, plan_id)
    result = await db.execute(
        select(SupportCategory).where(SupportCategory.plan_id == plan_id)
    )
    return result.scalars().all()


async def create_support_category(
    db: AsyncSession, plan_id: uuid.UUID, data: SupportCategoryIn
) -> SupportCategory:
    """Add a support category to a plan; raise 404 if plan not found."""
    await get_plan_by_id(db, plan_id)
    category = SupportCategory(plan_id=plan_id, **data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def update_support_category(
    db: AsyncSession, plan_id: uuid.UUID, category_id: uuid.UUID, data: SupportCategoryUpdate
) -> SupportCategory:
    """Update support category budget fields; raise 404 if not found or not part of the plan."""
    result = await db.execute(
        select(SupportCategory).where(
            SupportCategory.id == category_id,
            SupportCategory.plan_id == plan_id,
        )
    )
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support category not found",
        )
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    await db.commit()
    await db.refresh(category)
    return category
