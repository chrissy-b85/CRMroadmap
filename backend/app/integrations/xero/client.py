"""Xero API client using OAuth2 PKCE flow."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import urllib.parse
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import httpx

from app.integrations.xero.config import (
    XERO_CLIENT_ID,
    XERO_CLIENT_SECRET,
    XERO_REDIRECT_URI,
    XERO_WEBHOOK_KEY,
)
from app.integrations.xero.models import XeroBill, XeroContact, XeroTokens

if TYPE_CHECKING:
    from app.models.provider import Provider

logger = logging.getLogger(__name__)

XERO_AUTH_URL = "https://login.xero.com/identity/connect/authorize"
XERO_TOKEN_URL = "https://identity.xero.com/connect/token"
XERO_API_BASE = "https://api.xero.com/api.xro/2.0"
XERO_CONNECTIONS_URL = "https://api.xero.com/connections"
XERO_SCOPES = "offline_access accounting.transactions accounting.contacts"


class XeroClient:
    """Async Xero API client."""

    def __init__(
        self,
        access_token: str | None = None,
        refresh_token: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.tenant_id = tenant_id

    async def get_auth_url(self) -> tuple[str, str]:
        """Generate OAuth2 authorisation URL and state token for Xero connection.

        Returns:
            Tuple of (auth_url, state) where *state* should be stored in the
            session so it can be validated in the callback.
        """
        state = secrets.token_urlsafe(32)
        params = {
            "response_type": "code",
            "client_id": XERO_CLIENT_ID,
            "redirect_uri": XERO_REDIRECT_URI,
            "scope": XERO_SCOPES,
            "state": state,
        }
        url = f"{XERO_AUTH_URL}?{urllib.parse.urlencode(params)}"
        return url, state

    async def exchange_code(self, code: str) -> XeroTokens:
        """Exchange auth code for access + refresh tokens."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                XERO_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": XERO_REDIRECT_URI,
                },
                auth=(XERO_CLIENT_ID, XERO_CLIENT_SECRET),
            )
            resp.raise_for_status()
            data = resp.json()

        tokens = XeroTokens(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data.get("expires_in", 1800),
        )
        self.access_token = tokens.access_token
        self.refresh_token = tokens.refresh_token
        return tokens

    async def refresh_access_token(self, refresh_token: str) -> XeroTokens:
        """Refresh expired access token using the stored refresh token."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                XERO_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                auth=(XERO_CLIENT_ID, XERO_CLIENT_SECRET),
            )
            resp.raise_for_status()
            data = resp.json()

        tokens = XeroTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            expires_in=data.get("expires_in", 1800),
        )
        self.access_token = tokens.access_token
        self.refresh_token = tokens.refresh_token
        return tokens

    async def get_tenant_id(self) -> str:
        """Get connected Xero organisation tenant ID."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                XERO_CONNECTIONS_URL,
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
            resp.raise_for_status()
            connections = resp.json()

        if not connections:
            raise ValueError("No Xero tenants connected")
        tenant_id: str = connections[0]["tenantId"]
        self.tenant_id = tenant_id
        return tenant_id

    def _api_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Xero-Tenant-Id": self.tenant_id or "",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def create_bill(self, invoice_data: dict) -> XeroBill:
        """Create a Bill in Xero from approved CRM invoice data.

        *invoice_data* must include:
          - ``invoice_number`` (str)
          - ``contact_id``     (str)
          - ``date``           (str, ISO-8601)
          - ``due_date``       (str, ISO-8601, optional)
          - ``line_items``     (list of dicts with keys: description,
                               quantity, unit_amount, account_code)
        """
        payload: dict[str, Any] = {
            "Type": "ACCPAY",
            "Contact": {"ContactID": invoice_data["contact_id"]},
            "InvoiceNumber": invoice_data.get("invoice_number", ""),
            "Date": invoice_data.get("date", ""),
            "Status": "SUBMITTED",
            "LineItems": [
                {
                    "Description": item.get("description", ""),
                    "Quantity": float(item.get("quantity", 1)),
                    "UnitAmount": float(item.get("unit_amount", 0)),
                    "AccountCode": item.get("account_code", "200"),
                }
                for item in invoice_data.get("line_items", [])
            ],
        }
        if invoice_data.get("due_date"):
            payload["DueDate"] = invoice_data["due_date"]

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{XERO_API_BASE}/Invoices",
                headers=self._api_headers(),
                content=json.dumps({"Invoices": [payload]}),
            )
            resp.raise_for_status()
            data = resp.json()

        return self._parse_bill(data["Invoices"][0])

    async def get_bill(self, xero_invoice_id: str) -> XeroBill:
        """Get bill status from Xero."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{XERO_API_BASE}/Invoices/{xero_invoice_id}",
                headers=self._api_headers(),
            )
            resp.raise_for_status()
            data = resp.json()

        return self._parse_bill(data["Invoices"][0])

    async def void_bill(self, xero_invoice_id: str) -> None:
        """Void a bill in Xero."""
        payload = {"Invoices": [{"InvoiceID": xero_invoice_id, "Status": "VOIDED"}]}
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{XERO_API_BASE}/Invoices/{xero_invoice_id}",
                headers=self._api_headers(),
                content=json.dumps(payload),
            )
            resp.raise_for_status()

    async def get_contacts(self, search: str) -> list[XeroContact]:
        """Search for Xero contacts by name or tax number."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{XERO_API_BASE}/Contacts",
                headers=self._api_headers(),
                params={"searchTerm": search},
            )
            resp.raise_for_status()
            data = resp.json()

        return [self._parse_contact(c) for c in data.get("Contacts", [])]

    async def create_contact(self, provider: "Provider") -> XeroContact:
        """Create Xero contact from CRM provider."""
        payload = {
            "Contacts": [
                {
                    "Name": provider.business_name,
                    "TaxNumber": provider.abn,
                }
            ]
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{XERO_API_BASE}/Contacts",
                headers=self._api_headers(),
                content=json.dumps(payload),
            )
            resp.raise_for_status()
            data = resp.json()

        return self._parse_contact(data["Contacts"][0])

    @staticmethod
    def _parse_bill(data: dict) -> XeroBill:
        return XeroBill(
            xero_invoice_id=data["InvoiceID"],
            invoice_number=data.get("InvoiceNumber", ""),
            status=data.get("Status", ""),
            amount_due=Decimal(str(data.get("AmountDue", 0))),
            amount_paid=Decimal(str(data.get("AmountPaid", 0))),
            contact_id=data.get("Contact", {}).get("ContactID", ""),
        )

    @staticmethod
    def _parse_contact(data: dict) -> XeroContact:
        return XeroContact(
            contact_id=data["ContactID"],
            name=data.get("Name", ""),
            tax_number=data.get("TaxNumber"),
        )

    @staticmethod
    def validate_webhook_signature(payload: bytes, signature_header: str) -> bool:
        """Validate Xero webhook HMAC-SHA256 signature.

        Xero computes ``HMAC-SHA256(XERO_WEBHOOK_KEY, payload)`` and sends the
        result as a base64-encoded string in the ``x-xero-signature`` header.
        """
        import base64

        if not XERO_WEBHOOK_KEY:
            return False
        expected = base64.b64encode(
            hmac.new(
                XERO_WEBHOOK_KEY.encode(),
                payload,
                hashlib.sha256,
            ).digest()
        ).decode()
        return hmac.compare_digest(expected, signature_header)
