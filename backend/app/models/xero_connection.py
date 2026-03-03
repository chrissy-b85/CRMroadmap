"""SQLAlchemy model for storing Xero OAuth tokens."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin


class XeroConnection(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "xero_connections"

    tenant_id = Column(String(100), nullable=False)
    access_token = Column(String(2048), nullable=False)  # encrypted at rest
    refresh_token = Column(String(2048), nullable=False)  # encrypted at rest
    token_expiry = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
