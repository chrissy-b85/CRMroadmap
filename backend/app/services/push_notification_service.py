"""Web Push notification service for participant invoice approval requests."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def save_push_subscription(
    db: AsyncSession, participant_id: UUID, subscription: dict
) -> None:
    """Persist (or replace) a participant's Web Push subscription in the DB."""
    from app.models.push_subscription import PushSubscription

    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.participant_id == participant_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        existing.subscription = subscription
    else:
        db.add(PushSubscription(participant_id=participant_id, subscription=subscription))
    await db.commit()


async def get_push_subscription(
    db: AsyncSession, participant_id: UUID
) -> dict | None:
    """Retrieve the stored Web Push subscription for a participant, or None."""
    from app.models.push_subscription import PushSubscription

    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.participant_id == participant_id
        )
    )
    record = result.scalar_one_or_none()
    return record.subscription if record is not None else None


async def send_invoice_approval_request(
    db: AsyncSession, participant_id: UUID, invoice_id: UUID
) -> None:
    """Send a Web Push notification to a participant for a pending invoice.

    Uses the ``pywebpush`` library when available.  If the library is not
    installed or the participant has no registered subscription the call is a
    no-op (error is logged but not raised so callers are not disrupted).
    """
    subscription = await get_push_subscription(db, participant_id)
    if subscription is None:
        logger.debug(
            "No push subscription for participant %s; skipping notification",
            participant_id,
        )
        return

    import os

    vapid_private_key = os.getenv("VAPID_PRIVATE_KEY", "")
    vapid_claims_email = os.getenv("VAPID_CLAIMS_EMAIL", "mailto:admin@ndis-crm.example")

    if not vapid_private_key:
        logger.warning(
            "VAPID_PRIVATE_KEY not configured; skipping push notification for invoice %s",
            invoice_id,
        )
        return

    import json

    payload = json.dumps(
        {
            "title": "Invoice awaiting your approval",
            "body": "A new invoice has been submitted on your behalf and requires your review.",
            "url": f"/portal/invoices/{invoice_id}",
        }
    )

    try:
        from pywebpush import WebPushException, webpush  # type: ignore[import]

        webpush(
            subscription_info=subscription,
            data=payload,
            vapid_private_key=vapid_private_key,
            vapid_claims={"sub": vapid_claims_email},
        )
    except WebPushException as exc:
        logger.warning(
            "Web Push delivery failed for invoice %s: %s", invoice_id, exc
        )
    except Exception:  # noqa: BLE001 — unexpected errors must not disrupt callers
        logger.warning(
            "Unexpected error sending push notification for invoice %s",
            invoice_id,
            exc_info=True,
        )
