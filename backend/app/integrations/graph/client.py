"""Authenticated Microsoft Graph API client using app-only (client credentials) auth."""

from __future__ import annotations

import asyncio
import base64
import time
from typing import Any

import urllib.request
import urllib.parse
import urllib.error
import json

from app.integrations.graph.config import (
    GRAPH_CLIENT_ID,
    GRAPH_CLIENT_SECRET,
    GRAPH_CORRESPONDENCE_FOLDER_ID,
    GRAPH_FROM_MAILBOX,
    GRAPH_SHARED_MAILBOX,
    GRAPH_TENANT_ID,
)

_GRAPH_BASE = "https://graph.microsoft.com/v1.0"
_TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"


class GraphClient:
    """Microsoft Graph API client with token caching."""

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def _fetch_token(self) -> str:
        """Acquire an app-only access token via client credentials flow."""
        url = _TOKEN_URL_TEMPLATE.format(tenant=GRAPH_TENANT_ID)
        data = urllib.parse.urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": GRAPH_CLIENT_ID,
                "client_secret": GRAPH_CLIENT_SECRET,
                "scope": "https://graph.microsoft.com/.default",
            }
        ).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            body: dict[str, Any] = json.loads(resp.read())
        self._access_token = body["access_token"]
        self._token_expiry = time.time() + int(body.get("expires_in", 3600)) - 60
        return self._access_token

    def _get_token(self) -> str:
        if not self._access_token or time.time() >= self._token_expiry:
            return self._fetch_token()
        return self._access_token

    def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
    ) -> Any:
        """Synchronous helper that executes a Graph API request."""
        token = self._get_token()
        url = f"{_GRAPH_BASE}{path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Graph API {method} {path} failed: {exc.code} {exc.reason}"
            ) from exc

    # ------------------------------------------------------------------
    # Public async interface (run sync HTTP in executor to stay async-safe)
    # ------------------------------------------------------------------

    async def _async_request(
        self, method: str, path: str, body: dict | None = None
    ) -> Any:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._request(method, path, body)
        )

    async def get_inbox_messages(self, folder_id: str, top: int = 50) -> list[dict]:
        """Return up to *top* unread messages from a mailbox folder."""
        path = (
            f"/users/{GRAPH_SHARED_MAILBOX}/mailFolders/{folder_id}/messages"
            f"?$top={top}&$filter=isRead eq false"
        )
        result = await self._async_request("GET", path)
        return (result or {}).get("value", [])

    async def get_message_attachments(self, message_id: str) -> list[dict]:
        """Return all attachments for a message."""
        path = f"/users/{GRAPH_SHARED_MAILBOX}/messages/{message_id}/attachments"
        result = await self._async_request("GET", path)
        return (result or {}).get("value", [])

    async def download_attachment(self, message_id: str, attachment_id: str) -> bytes:
        """Download and return the raw bytes of an attachment."""
        path = f"/users/{GRAPH_SHARED_MAILBOX}/messages/{message_id}/attachments/{attachment_id}"
        result = await self._async_request("GET", path)
        content_bytes = (result or {}).get("contentBytes", "")
        return base64.b64decode(content_bytes)

    async def mark_message_as_read(self, message_id: str) -> None:
        """Patch a message to mark it as read."""
        path = f"/users/{GRAPH_SHARED_MAILBOX}/messages/{message_id}"
        await self._async_request("PATCH", path, {"isRead": True})

    async def move_message_to_folder(self, message_id: str, folder_id: str) -> None:
        """Move a message to the specified destination folder."""
        path = f"/users/{GRAPH_SHARED_MAILBOX}/messages/{message_id}/move"
        await self._async_request("POST", path, {"destinationId": folder_id})

    async def send_mail(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        attachment_bytes: bytes | None = None,
        attachment_name: str | None = None,
        attachment_content_type: str = "application/pdf",
    async def send_email(
        self,
        from_mailbox: str,
        to_emails: list[str],
        subject: str,
        html_body: str,
        attachments: list[dict] | None = None,
    ) -> str:
        """Send an email via Graph API and return the sent message ID.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            body_html: HTML body content.
            attachment_bytes: Optional binary attachment data.
            attachment_name: Filename for the attachment.
            attachment_content_type: MIME type of the attachment.

        Returns:
            The Graph API message ID of the sent message.
        """
        import base64

        message: dict = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body_html},
            "toRecipients": [{"emailAddress": {"address": to_email}}],
        }

        if attachment_bytes is not None and attachment_name is not None:
            message["attachments"] = [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": attachment_name,
                    "contentType": attachment_content_type,
                    "contentBytes": base64.b64encode(attachment_bytes).decode(),
                }
            ]

        path = f"/users/{GRAPH_SHARED_MAILBOX}/sendMail"
        await self._async_request(
            "POST", path, {"message": message, "saveToSentItems": True}
        )

        # Graph sendMail returns 202 with no body; retrieve the last sent
        # item for the message ID.
        sent_path = (
            f"/users/{GRAPH_SHARED_MAILBOX}/mailFolders/SentItems/messages"
            from_mailbox: The shared mailbox address to send from.
            to_emails: List of recipient email addresses.
            subject: Email subject line.
            html_body: HTML content of the email body.
            attachments: Optional list of attachment dicts with keys
                ``name``, ``contentType``, and ``contentBytes`` (base64).

        Returns:
            The Graph API messageId of the sent message.
        """
        message: dict[str, Any] = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": [
                {"emailAddress": {"address": addr}} for addr in to_emails
            ],
        }
        if attachments:
            message["attachments"] = [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": att["name"],
                    "contentType": att.get("contentType", "application/octet-stream"),
                    "contentBytes": att["contentBytes"],
                }
                for att in attachments
            ]
        payload = {"message": message, "saveToSentItems": True}
        path = f"/users/{from_mailbox}/sendMail"
        await self._async_request("POST", path, payload)
        # Graph's sendMail returns 202 with no body; reconstruct a pseudo-ID
        # by querying the most recent sent item.
        sent_path = (
            f"/users/{from_mailbox}/mailFolders/SentItems/messages"
            "?$top=1&$orderby=sentDateTime desc&$select=id"
        )
        result = await self._async_request("GET", sent_path)
        items = (result or {}).get("value", [])
        return items[0]["id"] if items else ""

    async def get_correspondence_folder_messages(self, top: int = 50) -> list[dict]:
        """Return up to *top* unread messages from the correspondence folder.

        Uses ``GRAPH_CORRESPONDENCE_FOLDER_ID`` from config; falls back to
        ``Correspondence`` as a well-known folder name if not configured.
        """
        folder = GRAPH_CORRESPONDENCE_FOLDER_ID or "Correspondence"
        path = (
            f"/users/{GRAPH_SHARED_MAILBOX}/mailFolders/{folder}/messages"
            f"?$top={top}&$filter=isRead eq false"
        )
        result = await self._async_request("GET", path)
        return (result or {}).get("value", [])
