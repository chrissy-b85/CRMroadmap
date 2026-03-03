"""Pydantic v2 schemas for Participant endpoints."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class ParticipantBase(BaseModel):
    ndis_number: str
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None


class ParticipantIn(ParticipantBase):
    pass


class ParticipantUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    is_active: bool | None = None


class ParticipantOut(ParticipantBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ParticipantListOut(BaseModel):
    items: list[ParticipantOut]
    total: int
    page: int
    page_size: int
