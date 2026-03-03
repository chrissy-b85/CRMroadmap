# Monthly Statement Generation

This document describes how NDIS participant monthly PDF statements are generated, stored, and delivered.

## Overview

Every month, each participant receives a professional A4 PDF statement summarising:
- All **APPROVED** invoices for the period
- Budget utilisation per support category
- Total amounts and GST breakdown

Statements are stored in Google Cloud Storage (GCS) and can be delivered via Outlook email using the Microsoft Graph API.

---

## Architecture

```
Celery Beat (1st of month, 02:00 AEST)
    └── generate_monthly_statements task
            └── statement_service.generate_all_monthly_statements()
                    ├── For each active participant with APPROVED invoices:
                    │       ├── Render HTML (Jinja2 template)
                    │       ├── Convert to PDF (WeasyPrint)
                    │       ├── Upload to GCS
                    │       └── Save StatementRecord to DB
                    └── (optionally) email each statement via Graph API
```

---

## Components

### Service: `backend/app/services/statement_service.py`

| Function | Description |
|---|---|
| `generate_monthly_statement(db, participant_id, year, month)` | Generate a single statement and return the `StatementRecord` |
| `generate_all_monthly_statements(db, year, month)` | Batch generate for all active participants; returns `{generated, skipped, failed}` |
| `get_statement(db, participant_id, year, month)` | Retrieve an existing statement record |
| `list_statements(db, participant_id)` | List all statements for a participant (newest first) |
| `email_statement(db, participant_id, year, month)` | Email a statement PDF to the participant via Graph API |

### Model: `backend/app/models/statement.py`

```python
class StatementRecord(Base):
    __tablename__ = 'statements'

    id: UUID                    # Primary key
    participant_id: UUID        # FK → participants.id
    year: int                   # Statement year
    month: int                  # Statement month (1–12)
    gcs_pdf_path: str           # gs://bucket/statements/{participant_id}/{year}-{month:02d}.pdf
    invoice_count: int          # Number of APPROVED invoices included
    total_amount: Decimal       # Sum of all invoice total_amount values
    generated_at: datetime      # When the PDF was generated
    emailed_at: datetime | None # When the email was sent (if applicable)
    email_message_id: str | None # Graph API message ID for the sent email
```

### PDF Template: `backend/app/templates/statements/monthly_statement.html`

A Jinja2 HTML template designed for WeasyPrint A4 output. Key sections:
- **Header**: Organisation logo, participant name, NDIS number, statement period
- **Summary**: Invoice count, total amount, GST, net amount
- **Budget utilisation table**: Per category — allocated, spent, remaining, % with visual bar
- **Invoice line items**: Date, number, provider, description, category, amounts, status
- **Footer**: Generated date, page numbers, organisation contact

To customise the template, edit `backend/app/templates/statements/monthly_statement.html`.
The organisation contact details can be set via the `ORG_CONTACT` environment variable.

### API Endpoints: `backend/app/routers/statements.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/statements/participants/{id}` | Any authenticated | List all statements for a participant |
| `GET` | `/api/v1/statements/participants/{id}/{year}/{month}` | Any authenticated | Get a specific statement with signed download URL |
| `POST` | `/api/v1/statements/participants/{id}/{year}/{month}/generate` | Admin | Manually generate a statement |
| `POST` | `/api/v1/statements/participants/{id}/{year}/{month}/email` | Admin/Coordinator | Email the statement to the participant |
| `POST` | `/api/v1/statements/batch/{year}/{month}` | Admin | Batch generate for all participants |
| `GET` | `/api/v1/statements/my-statements` | Participant | Portal: list own statements |

---

## GCS Storage

PDFs are stored in the invoices bucket under:
```
statements/{participant_id}/{year}-{month:02d}.pdf
```

Example: `statements/3fa85f64-5717-4562-b3fc-2c963f66afa6/2026-02.pdf`

Download URLs are signed GCS URLs with a 1-hour expiry, generated on each API request.

---

## Celery Schedule

The batch task runs on the 1st of each month at 02:00 (server time):

```python
# backend/app/worker/beat_schedule.py
'generate-monthly-statements': {
    'task': 'app.worker.tasks.generate_monthly_statements',
    'schedule': crontab(day_of_month=1, hour=2, minute=0),
}
```

The task generates statements for the **previous** month automatically.

To trigger generation manually, use the Admin API:
```bash
curl -X POST /api/v1/statements/batch/2026/1 \
  -H "Authorization: Bearer <admin-token>"
```

---

## Dependencies

- **WeasyPrint** (`weasyprint>=60.0`): HTML-to-PDF conversion. Requires system libraries on Linux:
  ```bash
  apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
  ```
- **Jinja2** (`jinja2>=3.1.0`): HTML template rendering.

---

## Frontend

### Participant Portal (`/portal/statements`)

Participants can view and download their monthly statements at `/portal/statements`.  
The page lists all statements (most recent first) with:
- Statement period (e.g. "February 2026")
- Invoice count
- Total amount
- Download PDF button

### Staff CRM (`/dashboard/participants/{id}`)

Staff can manage statements for a specific participant via the **Statements** tab:
- Table of all statements with download and email actions
- **Generate Statement** button for ad-hoc generation of the current month

---

## Testing

Run the statement tests:
```bash
cd backend
pytest tests/test_statements.py -v
```

Tests use mocked WeasyPrint, GCS, and Graph API calls so no external dependencies are needed.
