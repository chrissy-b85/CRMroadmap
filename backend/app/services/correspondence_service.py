"""Correspondence monitoring service.

Polls the shared Outlook 'Correspondence' mailbox folder for inbound emails,
matches senders to participant/provider records, and creates EmailThread records.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.graph.client import GraphClient
from app.integrations.graph.config import GRAPH_PROCESSED_FOLDER_ID
from app.models.audit_log import AuditLog
from app.models.email_thread import EmailThread
from app.models.participant import Participant
from app.models.provider import Provider

logger = logging.getLogger(__name__)


async def match_sender_to_record(
    db: AsyncSession, sender_email: str
) -> tuple[str, UUID] | None:
    """Try to match sender email to a participant or provider.

    Returns:
        A tuple of (``'participant'`` | ``'provider'``, record UUID) or ``None``
        if no match is found.
    """
    normalised = sender_email.strip().lower()

    part_result = await db.execute(
        select(Participant).where(
            Participant.email.ilike(normalised)
        )
    )
    participant = part_result.scalar_one_or_none()
    if participant is not None:
        return ("participant", participant.id)

    prov_result = await db.execute(
        select(Provider).where(
            Provider.email.ilike(normalised)
        )
    )
    provider = prov_result.scalar_one_or_none()
    if provider is not None:
        return ("provider", provider.id)

    return None


async def poll_correspondence_inbox(db: AsyncSession) -> dict:
    """Poll shared mailbox for new correspondence emails.

    Steps per email:
    1. Fetch unread emails from the 'Correspondence' folder
    2. Try to match sender to participant/provider
    3. Create an ``EmailThread`` record linked to the matched record
    4. Mark email as read and move to processed folder
    5. Write an audit log entry

    Returns:
        Dict with keys ``processed``, ``matched``, ``unmatched``.
    """
    graph = GraphClient()
    messages = await graph.get_correspondence_folder_messages()

    processed = 0
    matched = 0
    unmatched = 0

    for message in messages:
        try:
            message_id: str = message.get("id", "")
            subject: str = message.get("subject", "")
            from_field = (message.get("from") or {}).get("emailAddress") or {}
            sender_email: str = from_field.get("address", "")
            sender_name: Optional[str] = from_field.get("name")
            body_preview: Optional[str] = message.get("bodyPreview")
            has_attachments: bool = bool(message.get("hasAttachments", False))
            conversation_id: str = message.get("conversationId") or message_id

            received_str: str = message.get("receivedDateTime", "")
            received_at: datetime | None = None
            if received_str:
                try:
                    received_at = datetime.fromisoformat(
                        received_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    received_at = datetime.now(tz=timezone.utc)

            # Match sender to participant/provider
            participant_id: UUID | None = None
            provider_id: UUID | None = None
            match = await match_sender_to_record(db, sender_email)

            if match:
                record_type, record_id = match
                if record_type == "participant":
                    participant_id = record_id
                else:
                    provider_id = record_id
                matched += 1
            else:
                unmatched += 1

            thread = EmailThread(
                graph_message_id=message_id,
                graph_thread_id=conversation_id,
                subject=subject,
                sender_email=sender_email,
                sender_name=sender_name,
                received_at=received_at,
                direction="inbound",
                body_preview=body_preview,
                has_attachments=has_attachments,
                participant_id=participant_id,
                provider_id=provider_id,
            )
            db.add(thread)
            await db.flush()

            audit = AuditLog(
                action="correspondence_received",
                entity_type="EmailThread",
                entity_id=thread.id,
                new_values={
                    "sender_email": sender_email,
                    "subject": subject,
                    "matched": match is not None,
                },
            )
            db.add(audit)

            # Mark as read and move to processed folder
            try:
                await graph.mark_message_as_read(message_id)
                if GRAPH_PROCESSED_FOLDER_ID:
                    await graph.move_message_to_folder(
                        message_id, GRAPH_PROCESSED_FOLDER_ID
                    )
            except Exception:  # noqa: BLE001
                logger.warning(
                    "Could not mark/move correspondence message %s",
                    message_id,
                    exc_info=True,
                )

            processed += 1

        except Exception:  # noqa: BLE001
            logger.exception(
                "Failed to process correspondence message %s", message.get("id")
            )

    await db.commit()
    return {"processed": processed, "matched": matched, "unmatched": unmatched}
