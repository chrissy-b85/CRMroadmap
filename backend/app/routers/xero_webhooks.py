"""FastAPI router for Xero webhook events."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.db import get_db
from app.integrations.xero.client import XeroClient

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Xero Webhooks"])


@router.post("/webhooks/xero", status_code=status.HTTP_200_OK)
async def xero_webhook(request: Request):
    """Receive and process Xero webhook events.

    - Validates the HMAC-SHA256 signature using ``XERO_WEBHOOK_KEY``.
    - Handles ``PaymentCreated`` events → marks CRM invoice as PAID.
    - Handles ``InvoiceUpdated`` events → syncs status changes.

    Xero performs an *intent to receive* validation by sending an empty POST
    and expecting a 200 response, so we return 200 even when the body is empty.
    """
    payload = await request.body()

    # Intent-to-receive: empty body
    if not payload:
        return {"detail": "ok"}

    signature = request.headers.get("x-xero-signature", "")
    if not XeroClient.validate_webhook_signature(payload, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    try:
        import json

        body = json.loads(payload)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    events = body.get("events", [])
    async for db in get_db():
        from app.services.xero_sync_service import sync_payment_from_xero

        for event in events:
            event_type = event.get("eventType", "")
            resource_id = event.get("resourceId", "")

            if not resource_id:
                continue

            if event_type == "CREATE" and event.get("eventCategory") == "PAYMENT":
                try:
                    await sync_payment_from_xero(db, resource_id)
                    logger.info(
                        "Payment synced for Xero resource %s", resource_id
                    )
                except ValueError:
                    logger.warning(
                        "No CRM invoice found for Xero resource %s", resource_id
                    )
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "Error syncing payment for Xero resource %s", resource_id
                    )

            elif event_type == "UPDATE" and event.get("eventCategory") == "INVOICE":
                # Check if the bill is now PAID
                try:
                    from app.integrations.xero.client import XeroClient as _XC
                    from app.models.xero_connection import XeroConnection
                    from sqlalchemy import select

                    conn_result = await db.execute(
                        select(XeroConnection)
                        .where(XeroConnection.is_active.is_(True))
                        .limit(1)
                    )
                    conn = conn_result.scalar_one_or_none()
                    if conn:
                        xero = _XC(
                            access_token=conn.access_token,
                            tenant_id=conn.tenant_id,
                        )
                        bill = await xero.get_bill(resource_id)
                        if bill.status == "PAID":
                            await sync_payment_from_xero(db, resource_id)
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "Error handling InvoiceUpdated for Xero resource %s",
                        resource_id,
                    )

    return {"detail": "ok"}
