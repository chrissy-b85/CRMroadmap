"""FastAPI router for budget tracking endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_role
from app.db import get_db
from app.schemas.budget import BudgetAlert, BurnRate, ParticipantBudgetOverview, PlanBudgetSummary
from app.services import budget_tracking_service as svc

router = APIRouter(prefix="/budget", tags=["Budget"])


@router.get("/plans/{plan_id}/summary", response_model=PlanBudgetSummary)
async def get_plan_budget_summary(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Real-time budget summary for a plan with alerts."""
    summary = await svc.get_plan_budget_summary(db, plan_id)
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return summary


@router.get("/plans/{plan_id}/burn-rate", response_model=list[BurnRate])
async def get_burn_rates(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Burn rate analysis per support category."""
    from app.models.plan import Plan
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Plan).options(selectinload(Plan.support_categories)).where(Plan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    burn_rates = []
    for cat in plan.support_categories:
        br = await svc.calculate_burn_rate(db, plan_id, cat.id)
        if br is not None:
            burn_rates.append(br)
    return burn_rates


@router.get("/participants/{participant_id}/overview", response_model=ParticipantBudgetOverview)
async def get_participant_budget_overview(
    participant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Budget overview across all plans for a participant."""
    overview = await svc.get_participant_budget_overview(db, participant_id)
    if overview is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found"
        )
    return overview


@router.get("/alerts", response_model=list[BudgetAlert])
async def get_all_budget_alerts(
    severity: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all active budget alerts across all participants (Coordinator view)."""
    return await svc.get_all_active_plan_alerts(db, severity)


@router.post("/plans/{plan_id}/recalculate", status_code=status.HTTP_202_ACCEPTED)
async def recalculate_budget(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Admin")),
):
    """Trigger budget recalculation for a plan (Admin only)."""
    await svc.recalculate_budget_spent(db, plan_id)
    return {"detail": "Budget recalculation complete", "plan_id": str(plan_id)}
