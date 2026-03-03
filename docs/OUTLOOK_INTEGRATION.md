# Outlook Integration via Microsoft Graph API

This document describes how to configure the NDIS CRM's Microsoft Outlook integration,
which provides:

- **Outbound email notifications** — automated emails to participants, providers, and staff
- **Inbound correspondence monitoring** — polling a shared mailbox and auto-logging emails

---

## Microsoft Graph App Registration

### Required Scopes (Application permissions)

| Permission | Purpose |
|---|---|
| `Mail.Send` | Send outbound notification emails from the shared mailbox |
| `Mail.ReadWrite` | Read, mark as read, and move inbound correspondence emails |

### Steps

1. Go to [Azure Portal → App registrations](https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps)
2. Click **New registration**
3. Enter a name (e.g. `NDIS CRM Graph Integration`) and select **Accounts in this organizational directory only**
4. After creation, go to **Certificates & secrets** → **New client secret** — copy the value immediately
5. Go to **API permissions** → **Add a permission** → **Microsoft Graph** → **Application permissions**
6. Add `Mail.Send` and `Mail.ReadWrite`
7. Click **Grant admin consent**
8. Note down:
   - **Application (client) ID** → `GRAPH_CLIENT_ID`
   - **Directory (tenant) ID** → `GRAPH_TENANT_ID`
   - **Client secret value** → `GRAPH_CLIENT_SECRET`

---

## Configuring Shared Mailboxes

The integration uses two mailbox addresses:

| Variable | Purpose | Example |
|---|---|---|
| `GRAPH_SHARED_MAILBOX` | Invoice ingestion inbox (Sprint 5) | `invoices@your-org.com.au` |
| `GRAPH_FROM_MAILBOX` | Outbound notification sender | `notifications@your-org.com.au` |

Both mailboxes must be accessible by the registered app. Grant the app **Full Access**
to each shared mailbox via Exchange Admin Center → **Mailboxes** → select mailbox →
**Mailbox delegation** → **Full Access**.

### Correspondence Folder

Create a mail folder called `Correspondence` (or any name) in the shared mailbox and
configure its ID:

```
GRAPH_CORRESPONDENCE_FOLDER_ID=<folder-id-from-graph-api>
```

To find the folder ID, call:
```
GET https://graph.microsoft.com/v1.0/users/{mailbox}/mailFolders
```

The `GRAPH_PROCESSED_FOLDER_ID` folder is used to move processed messages out of
the active inbox after they have been ingested/logged.

---

## Environment Variables

Add these to `backend/.env` (see `backend/.env.example` for the full list):

```dotenv
GRAPH_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
GRAPH_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
GRAPH_CLIENT_SECRET=your-client-secret
GRAPH_SHARED_MAILBOX=invoices@your-org.com.au
GRAPH_FROM_MAILBOX=notifications@your-org.com.au
GRAPH_PROCESSED_FOLDER_ID=AAMkAGI...
GRAPH_CORRESPONDENCE_FOLDER_ID=AAMkAGJ...
```

---

## Email Template Customisation

Templates are located in `backend/app/templates/email/` and use [Jinja2](https://jinja.palletsprojects.com/) syntax.

| File | Purpose |
|---|---|
| `_base.html` | Base layout with header, footer, and branding |
| `invoice_processed.html` | Invoice received, awaiting approval |
| `invoice_approved.html` | Invoice approved by staff |
| `invoice_rejected.html` | Invoice rejected with reason |
| `info_requested.html` | More information requested from provider |
| `plan_expiry_warning.html` | Plan expiring within 30 days |
| `low_budget_alert.html` | Support category at 75%/90% utilisation |

To customise branding, edit the `<style>` block and header section in `_base.html`.
Each template `{% extends "_base.html" %}` and fills the `{% block content %}` block.

### Available template variables

| Template | Variables |
|---|---|
| `invoice_processed.html` | `participant_name`, `invoice` |
| `invoice_approved.html` | `participant_name`, `invoice` |
| `invoice_rejected.html` | `participant_name`, `invoice`, `reason` |
| `info_requested.html` | `invoice`, `message` |
| `plan_expiry_warning.html` | `participant_name`, `plan`, `days_remaining` |
| `low_budget_alert.html` | `participant_name`, `category_name`, `utilisation_percent` |

---

## Notification Event Mapping

| Event | Method | Recipients |
|---|---|---|
| Invoice OCR-processed | `send_invoice_processed_notification` | Participant |
| Invoice approved by staff | `send_invoice_approved_notification` | Participant |
| Invoice rejected | `send_invoice_rejected_notification` | Participant + Provider |
| Info requested from provider | `send_info_requested_notification` | Provider |
| Plan expiring in ≤30 days | `send_plan_expiry_warning` | Participant |
| Budget category ≥75% or ≥90% | `send_low_budget_alert` | Participant |
| Monthly statement | `send_monthly_statement` | Participant (PDF attachment) |

Notifications for invoice events are triggered as FastAPI background tasks from
`backend/app/routers/invoices.py` (approve, reject, request-info endpoints).

Scheduled notifications run via Celery beat (see `backend/app/worker/beat_schedule.py`):

| Task | Schedule |
|---|---|
| `poll_correspondence_inbox` | Every 15 minutes |
| `send_budget_alert_emails` | Daily at 08:00 |
| `send_plan_expiry_warnings` | Daily at 08:15 |

---

## Correspondence Monitoring

The `poll_correspondence_inbox` task:
1. Fetches unread emails from the `Correspondence` mailbox folder
2. Matches each sender's email address against `participants.email` or `providers.email`
3. Creates an `EmailThread` record linked to the matched participant/provider
4. Marks the email as read and moves it to the processed folder
5. Writes an `AuditLog` entry with action `correspondence_received`

Unmatched senders are still logged as `EmailThread` records with `participant_id=NULL`
and `provider_id=NULL` for manual review.

### Correspondence History API

```
GET /api/v1/participants/{participant_id}/correspondence
GET /api/v1/providers/{provider_id}/correspondence
```

Both endpoints require a valid Auth0 JWT and return `EmailThreadOut` objects ordered
by `received_at` descending.
