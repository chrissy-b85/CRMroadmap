"""Pydantic schemas for EmailThread / correspondence endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EmailThreadOut(BaseModel):
    id: UUID
    graph_message_id: str
    graph_thread_id: str | None = None
    subject: str | None = None
    sender_email: str | None = None
    sender_name: str | None = None
    received_at: datetime | None = None
    direction: str
    body_preview: str | None = None
    has_attachments: bool
    participant_id: UUID | None = None
    provider_id: UUID | None = None
    invoice_id: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
