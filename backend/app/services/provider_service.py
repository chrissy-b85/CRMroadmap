"""Async service functions for Provider CRUD operations."""
import uuid
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider import Provider
from app.schemas.provider import ProviderIn, ProviderUpdate


async def get_providers(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    active_only: bool = False,
) -> tuple[Sequence[Provider], int]:
    """Return a paginated list of providers with optional name/ABN search."""
    query = select(Provider)
    count_query = select(func.count()).select_from(Provider)

    if active_only:
        query = query.where(Provider.is_active.is_(True))
        count_query = count_query.where(Provider.is_active.is_(True))

    if search:
        like = f"%{search}%"
        condition = or_(
            Provider.business_name.ilike(like),
            Provider.abn.ilike(like),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    items = result.scalars().all()

    return items, total


async def get_provider_by_id(db: AsyncSession, provider_id: uuid.UUID) -> Provider:
    """Fetch a single provider; raise 404 if not found."""
    result = await db.execute(
        select(Provider).where(Provider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    return provider


async def get_provider_by_abn(db: AsyncSession, abn: str) -> Provider:
    """Fetch a provider by ABN; raise 404 if not found."""
    result = await db.execute(select(Provider).where(Provider.abn == abn))
    provider = result.scalar_one_or_none()
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    return provider


async def create_provider(db: AsyncSession, data: ProviderIn) -> Provider:
    """Create a new provider; raise 409 if ABN already exists."""
    existing = await db.execute(select(Provider).where(Provider.abn == data.abn))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A provider with this ABN already exists",
        )
    provider = Provider(**data.model_dump())
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    return provider


async def update_provider(
    db: AsyncSession, provider_id: uuid.UUID, data: ProviderUpdate
) -> Provider:
    """Partially update a provider's fields."""
    provider = await get_provider_by_id(db, provider_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(provider, field, value)
    await db.commit()
    await db.refresh(provider)
    return provider


async def deactivate_provider(db: AsyncSession, provider_id: uuid.UUID) -> None:
    """Soft-delete a provider by setting is_active=False."""
    provider = await get_provider_by_id(db, provider_id)
    provider.is_active = False
    await db.commit()
