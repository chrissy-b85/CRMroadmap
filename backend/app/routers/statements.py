"""FastAPI router for statement management endpoints."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_role
from app.auth.participant import get_current_participant
from app.db import get_db
from app.models.statement import StatementRecord
from app.schemas.statement import StatementOut
from app.services.statement_service import (
    email_statement,
    generate_all_monthly_statements,
    generate_monthly_statement,
    get_statement,
    list_statements,
)

router = APIRouter(prefix="/statements", tags=["Statements"])


async def _to_statement_out(record: StatementRecord) -> StatementOut:
    """Convert a StatementRecord to StatementOut with a signed URL."""
    from app.integrations.gcs.client import GCSClient

    try:
        gcs = GCSClient()
        download_url = await gcs.get_signed_url(record.gcs_pdf_path)
    except Exception:  # noqa: BLE001
        download_url = record.gcs_pdf_path  # Fall back to raw GCS path

    return StatementOut.model_validate(
        {
            "id": record.id,
            "participant_id": record.participant_id,
            "year": record.year,
            "month": record.month,
            "gcs_pdf_path": record.gcs_pdf_path,
            "download_url": download_url,
            "invoice_count": record.invoice_count,
            "total_amount": record.total_amount,
            "generated_at": record.generated_at,
            "emailed_at": record.emailed_at,
        }
    )


@router.get("/participants/{participant_id}", response_model=list[StatementOut])
async def list_participant_statements(
    participant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[StatementOut]:
    """List all available statements for a participant."""
    records = await list_statements(db, participant_id)
    return [await _to_statement_out(r) for r in records]


@router.get(
    "/participants/{participant_id}/{year}/{month}", response_model=StatementOut
)
async def get_participant_statement(
    participant_id: UUID,
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> StatementOut:
    """Get a specific month's statement with a signed GCS download URL."""
    record = await get_statement(db, participant_id, year, month)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Statement not found"
        )
    return await _to_statement_out(record)


@router.post(
    "/participants/{participant_id}/{year}/{month}/generate",
    response_model=StatementOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_generate_statement(
    participant_id: UUID,
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Admin")),
) -> StatementOut:
    """Manually trigger statement generation for a participant/month (Admin only)."""
    try:
        record = await generate_monthly_statement(db, participant_id, year, month)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return await _to_statement_out(record)


@router.post(
    "/participants/{participant_id}/{year}/{month}/email",
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_email_statement(
    participant_id: UUID,
    year: int,
    month: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
) -> dict:
    """Email a statement to the participant (Admin/Coordinator).

    Triggers the email as a background task and returns immediately.
    """

    async def _send():
        try:
            await email_statement(db, participant_id, year, month)
        except Exception:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).warning(
                "Failed to email statement for participant %s %d-%02d",
                participant_id,
                year,
                month,
                exc_info=True,
            )

    background_tasks.add_task(_send)
    return {"detail": "Statement email queued", "status": "accepted"}


@router.post(
    "/batch/{year}/{month}",
    status_code=status.HTTP_202_ACCEPTED,
)
async def batch_generate_all_statements(
    year: int,
    month: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Admin")),
) -> dict:
    """Trigger batch generation for all participants (Admin only)."""

    async def _run_batch():
        try:
            await generate_all_monthly_statements(db, year, month)
        except Exception:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).warning(
                "Batch statement generation failed for %d-%02d",
                year,
                month,
                exc_info=True,
            )

    background_tasks.add_task(_run_batch)
    return {
        "detail": f"Batch statement generation queued for {year}-{month:02d}",
        "status": "accepted",
    }


@router.get("/my-statements", response_model=list[StatementOut])
async def get_my_statements(
    db: AsyncSession = Depends(get_db),
    current_participant=Depends(get_current_participant),
) -> list[StatementOut]:
    """List all statements for the currently authenticated participant."""
    records = await list_statements(db, current_participant.id)
    return [await _to_statement_out(r) for r in records]