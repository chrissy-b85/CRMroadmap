# Invoice Ingestion Pipeline

This document describes the automated email invoice ingestion pipeline for the NDIS CRM.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Invoice Ingestion Pipeline                    │
│                                                                      │
│  Celery Beat (every 5 min)                                           │
│       │                                                              │
│       ▼                                                              │
│  GraphClient.get_inbox_messages()                                    │
│       │  Microsoft Graph API (Outlook shared mailbox)               │
│       ▼                                                              │
│  For each unread email with PDF attachment:                          │
│       │                                                              │
│       ├─► GraphClient.download_attachment()                          │
│       │        │                                                     │
│       │        ▼                                                     │
│       ├─► GCSClient.upload_pdf()  ──► GCS Bucket (invoices/)        │
│       │                                                              │
│       ├─► DocumentAIClient.parse_invoice()                           │
│       │        │  Google Document AI Invoice Parser                 │
│       │        ▼                                                     │
│       ├─► GCSClient.upload_json()  ──► GCS Bucket (invoices/ocr/)   │
│       │                                                              │
│       ├─► match_provider_by_abn()  ──► PostgreSQL (providers table) │
│       │                                                              │
│       ├─► Create Invoice + InvoiceLineItem + EmailThread in DB       │
│       │                                                              │
│       ├─► Write AuditLog entry                                       │
│       │                                                              │
│       └─► GraphClient.mark_message_as_read()                        │
│           GraphClient.move_message_to_folder()                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Microsoft Graph API Setup

### App Registration

1. Go to [Azure Portal](https://portal.azure.com) → **Azure Active Directory** → **App registrations** → **New registration**.
2. Enter a name (e.g. `ndis-crm-invoice-reader`) and click **Register**.
3. Note the **Application (client) ID** → set as `GRAPH_CLIENT_ID`.
4. Note the **Directory (tenant) ID** → set as `GRAPH_TENANT_ID`.
5. Go to **Certificates & secrets** → **New client secret** → copy the value → set as `GRAPH_CLIENT_SECRET`.

### API Permissions

Under **API permissions** → **Add a permission** → **Microsoft Graph** → **Application permissions**, add:

| Permission        | Purpose                          |
|-------------------|----------------------------------|
| `Mail.Read`       | Read messages from shared inbox  |
| `Mail.ReadWrite`  | Mark as read, move to folder     |

Click **Grant admin consent** for your organisation.

### Shared Mailbox

Set `GRAPH_SHARED_MAILBOX` to the email address of the shared invoice inbox (e.g. `invoices@your-org.com.au`).

To find the ID of the "Processed" folder, call:

```
GET https://graph.microsoft.com/v1.0/users/{mailbox}/mailFolders
```

Set the folder's `id` value as `GRAPH_PROCESSED_FOLDER_ID`.

## Google Document AI Setup

1. Enable the **Document AI API** in your GCP project.
2. Go to **Document AI** → **Processors** → **Create processor**.
3. Select **Invoice Parser** as the processor type.
4. Note the **Processor ID** → set as `DOCUMENT_AI_PROCESSOR_ID`.
5. Set `DOCUMENT_AI_PROJECT_ID` to your GCP project ID.
6. Set `DOCUMENT_AI_LOCATION` (default: `us`). Choose the region closest to your data.

The service account used by the application needs the **Document AI API User** IAM role.

## GCS Bucket Setup

1. Create a GCS bucket (e.g. `ndis-crm-invoices`).
2. Set `GCS_BUCKET_INVOICES` to the bucket name.
3. Grant the service account the **Storage Object Admin** role on this bucket.
4. Enable **Uniform bucket-level access** and configure a lifecycle policy as required.

Uploaded files follow this path convention:

```
invoices/
  participants/{participant_id}/{filename}.pdf      # matched participant
  unmatched/{filename}.pdf                          # unmatched invoices
  ocr/{filename}_ocr.json                           # Document AI result
```

## Running the Celery Worker Locally

### Prerequisites

- Redis running on `localhost:6379` (or update `CELERY_BROKER_URL`)
- All required environment variables set (copy `.env.example` to `.env`)

### Start the worker

```bash
cd backend
celery -A app.worker.celery_app worker --loglevel=info
```

### Start Celery Beat (scheduler)

```bash
cd backend
celery -A app.worker.beat_schedule beat --loglevel=info
```

This will poll the inbox every 5 minutes automatically.

## Triggering a Manual Inbox Poll

Using the API (requires Admin role):

```bash
curl -X POST http://localhost:8000/api/v1/invoices/ingest/trigger \
  -H "Authorization: Bearer <your-token>"
```

Response:

```json
{"detail": "Inbox poll triggered", "status": "accepted"}
```

The poll runs as a FastAPI background task and processes all unread emails in the inbox.

## Environment Variables Reference

| Variable                   | Description                                      | Example                        |
|----------------------------|--------------------------------------------------|-------------------------------|
| `GRAPH_TENANT_ID`          | Azure AD tenant ID                               | `xxxxxxxx-xxxx-xxxx-xxxx-xxxx`|
| `GRAPH_CLIENT_ID`          | Azure AD app client ID                           | `xxxxxxxx-xxxx-xxxx-xxxx-xxxx`|
| `GRAPH_CLIENT_SECRET`      | Azure AD app client secret                       | `secret`                      |
| `GRAPH_SHARED_MAILBOX`     | Shared inbox email address                       | `invoices@org.com.au`         |
| `GRAPH_PROCESSED_FOLDER_ID`| Outlook folder ID to move processed emails to    | `AAMkAGV...`                  |
| `DOCUMENT_AI_PROJECT_ID`   | GCP project ID                                   | `my-gcp-project`              |
| `DOCUMENT_AI_LOCATION`     | Document AI processor region                     | `us`                          |
| `DOCUMENT_AI_PROCESSOR_ID` | Document AI processor ID                         | `abc123def456`                |
| `GCS_BUCKET_INVOICES`      | GCS bucket name for invoice storage              | `ndis-crm-invoices`           |
| `CELERY_BROKER_URL`        | Celery broker URL (Redis)                        | `redis://localhost:6379/0`    |
| `CELERY_RESULT_BACKEND`    | Celery result backend URL (Redis)                | `redis://localhost:6379/0`    |
