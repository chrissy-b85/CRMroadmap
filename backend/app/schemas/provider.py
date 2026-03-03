"""Pydantic v2 schemas for Provider endpoints."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator

from app.utils.abn import validate_abn


class ProviderBase(BaseModel):
    business_name: str
    abn: str
    registration_group: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    bank_bsb: str | None = None
    bank_account: str | None = None
    bank_account_name: str | None = None
    xero_contact_id: str | None = None
    is_active: bool = True

    @field_validator("abn")
    @classmethod
    def validate_abn_format(cls, v: str) -> str:
        stripped = v.replace(" ", "")
        if not stripped.isdigit() or len(stripped) != 11:
            raise ValueError("ABN must be exactly 11 digits")
        if not validate_abn(stripped):
            raise ValueError("Invalid ABN — checksum failed")
        return stripped

    @field_validator("bank_bsb")
    @classmethod
    def validate_bsb(cls, v: str | None) -> str | None:
        if v is not None and v != "":
            if not v.isdigit() or len(v) != 6:
                raise ValueError("BSB must be exactly 6 digits")
        return v


class ProviderIn(ProviderBase):
    pass


class ProviderUpdate(BaseModel):
    business_name: str | None = None
    registration_group: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    bank_bsb: str | None = None
    bank_account: str | None = None
    bank_account_name: str | None = None
    xero_contact_id: str | None = None
    is_active: bool | None = None


class ProviderOut(BaseModel):
    id: UUID
    business_name: str
    abn: str
    registration_group: str | None
    email: str | None
    phone: str | None
    address: str | None
    bank_bsb: str | None
    bank_account_masked: str | None
    bank_account_name: str | None
    xero_contact_id: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def _mask_bank_account(cls, data):
        """Mask bank account to last 3 digits when building from an ORM object."""
        if hasattr(data, "bank_account"):
            account = data.bank_account
            masked = (
                f"***{account[-3:]}"
                if account and len(account) >= 3
                else account
            )
            # Build a plain dict for Pydantic to validate
            return {
                "id": data.id,
                "business_name": data.business_name,
                "abn": data.abn,
                "registration_group": data.registration_group,
                "email": data.email,
                "phone": data.phone,
                "address": data.address,
                "bank_bsb": data.bank_bsb,
                "bank_account_masked": masked,
                "bank_account_name": data.bank_account_name,
                "xero_contact_id": data.xero_contact_id,
                "is_active": data.is_active,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


class ProviderListOut(BaseModel):
    items: list[ProviderOut]
    total: int
    page: int
    page_size: int
