"""Email notification service for NDIS CRM.

Sends automated HTML emails via the Microsoft Graph API using Jinja2 templates.
Each method returns the Graph API messageId of the sent email.
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.integrations.graph.client import GraphClient
from app.integrations.graph.config import GRAPH_FROM_MAILBOX

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _render(template_name: str, **context: object) -> str:
    """Render a Jinja2 email template to an HTML string."""
    return _jinja_env.get_template(template_name).render(**context)


class EmailNotificationService:
    """Send transactional email notifications via Microsoft Graph."""

    def __init__(self) -> None:
        self._graph = GraphClient()
        self._from_mailbox = GRAPH_FROM_MAILBOX

    async def send_invoice_processed_notification(
        self, recipient_email: str, participant_name: str, invoice: object
    ) -> str:
        """Send email when invoice has been OCR-processed and needs approval."""
        html = _render(
            "invoice_processed.html",
            participant_name=participant_name,
            invoice=invoice,
        )
        return await self._graph.send_email(
            from_mailbox=self._from_mailbox,
            to_emails=[recipient_email],
            subject=f"Invoice Received – Awaiting Approval (#{getattr(invoice, 'invoice_number', '')})",
            html_body=html,
        )

    async def send_invoice_approved_notification(
        self, recipient_email: str, participant_name: str, invoice: object
    ) -> str:
        """Send email when invoice is approved by staff."""
        html = _render(
            "invoice_approved.html",
            participant_name=participant_name,
            invoice=invoice,
        )
        return await self._graph.send_email(
            from_mailbox=self._from_mailbox,
            to_emails=[recipient_email],
            subject=f"Invoice Approved (#{getattr(invoice, 'invoice_number', '')})",
            html_body=html,
        )

    async def send_invoice_rejected_notification(
        self,
        recipient_email: str,
        provider_email: str,
        invoice: object,
        reason: str,
        participant_name: str = "",
    ) -> str:
        """Send email when invoice is rejected, include reason."""
        html = _render(
            "invoice_rejected.html",
            participant_name=participant_name,
            invoice=invoice,
            reason=reason,
        )
        recipients = list({recipient_email, provider_email} - {""})
        return await self._graph.send_email(
            from_mailbox=self._from_mailbox,
            to_emails=recipients,
            subject=f"Invoice Rejected (#{getattr(invoice, 'invoice_number', '')})",
            html_body=html,
        )

    async def send_info_requested_notification(
        self, provider_email: str, invoice: object, message: str
    ) -> str:
        """Send email to provider requesting more info about an invoice."""
        html = _render(
            "info_requested.html",
            invoice=invoice,
            message=message,
        )
        return await self._graph.send_email(
            from_mailbox=self._from_mailbox,
            to_emails=[provider_email],
            subject=f"Additional Information Required (Invoice #{getattr(invoice, 'invoice_number', '')})",
            html_body=html,
        )

    async def send_plan_expiry_warning(
        self,
        participant_email: str,
        participant_name: str,
        plan: object,
        days_remaining: int,
    ) -> str:
        """Send warning email when plan expires in 30 days."""
        html = _render(
            "plan_expiry_warning.html",
            participant_name=participant_name,
            plan=plan,
            days_remaining=days_remaining,
        )
        return await self._graph.send_email(
            from_mailbox=self._from_mailbox,
            to_emails=[participant_email],
            subject=f"Your NDIS Plan Expires in {days_remaining} Days",
            html_body=html,
        )

    async def send_low_budget_alert(
        self,
        participant_email: str,
        participant_name: str,
        category_name: str,
        utilisation_percent: float,
    ) -> str:
        """Send alert when support category reaches 75% or 90% utilisation."""
        html = _render(
            "low_budget_alert.html",
            participant_name=participant_name,
            category_name=category_name,
            utilisation_percent=utilisation_percent,
        )
        level = "Critical" if utilisation_percent >= 90 else "Warning"
        return await self._graph.send_email(
            from_mailbox=self._from_mailbox,
            to_emails=[participant_email],
            subject=f"Budget {level}: {category_name} at {utilisation_percent:.0f}%",
            html_body=html,
        )

    async def send_monthly_statement(
        self,
        participant_email: str,
        participant_name: str,
        statement_pdf_bytes: bytes,
        month: str,
    ) -> str:
        """Send monthly statement PDF as email attachment."""
        html = _render(
            "invoice_approved.html",
            participant_name=participant_name,
            invoice=type("_Stub", (), {"invoice_number": month, "invoice_date": month, "total_amount": 0})(),
        )
        attachment = {
            "name": f"statement_{month}.pdf",
            "contentType": "application/pdf",
            "contentBytes": base64.b64encode(statement_pdf_bytes).decode(),
        }
        return await self._graph.send_email(
            from_mailbox=self._from_mailbox,
            to_emails=[participant_email],
            subject=f"Your NDIS Monthly Statement – {month}",
            html_body=html,
            attachments=[attachment],
        )
