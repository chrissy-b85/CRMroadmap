"""FastAPI router for provider management endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_role
from app.db import get_db
from app.schemas.provider import (
    ProviderIn,
    ProviderListOut,
    ProviderOut,
    ProviderUpdate,
)
from app.services import provider_service as svc

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get("/", response_model=ProviderListOut)
async def list_providers(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all providers with pagination and optional search by name or ABN."""
    items, total = await svc.get_providers(db, page, page_size, search, active_only)
    return ProviderListOut(
        items=[ProviderOut.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=ProviderOut, status_code=status.HTTP_201_CREATED)
async def create_provider(
    data: ProviderIn,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Create a new provider. Requires Coordinator or Admin role."""
    provider = await svc.create_provider(db, data)
    return ProviderOut.model_validate(provider)


@router.get("/abn/{abn}", response_model=ProviderOut)
async def get_provider_by_abn(
    abn: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Look up a provider by ABN."""
    provider = await svc.get_provider_by_abn(db, abn)
    return ProviderOut.model_validate(provider)


@router.get("/{provider_id}", response_model=ProviderOut)
async def get_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single provider by ID."""
    provider = await svc.get_provider_by_id(db, provider_id)
    return ProviderOut.model_validate(provider)


@router.patch("/{provider_id}", response_model=ProviderOut)
async def update_provider(
    provider_id: UUID,
    data: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Update provider details."""
    provider = await svc.update_provider(db, provider_id, data)
    return ProviderOut.model_validate(provider)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Admin")),
):
    """Deactivate a provider (soft delete). Requires Admin role."""
    await svc.deactivate_provider(db, provider_id)
