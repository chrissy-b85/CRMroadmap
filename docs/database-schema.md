# Database Schema

This document describes the PostgreSQL database schema for the NDIS CRM, implemented with SQLAlchemy 2.0 and managed by Alembic.

## ERD Overview

```
participants
    │
    ├──< plans
    │        │
    │        └──< support_categories
    │                    │
    │                    └──< invoice_line_items >──┐
    │                                               │
    ├──< invoices >─────────────────────────────────┘
    │        │
    │        ├──< invoice_line_items
    │        ├──< documents
    │        └──> email_threads >──< providers
    │
    └──< documents

users
    ├──> invoices (reviewed_by)
    ├──> documents (uploaded_by)
    └──< audit_log
```

## Tables

### `participants`
Stores NDIS participant (client) information.

| Column           | Type          | Notes                         |
|------------------|---------------|-------------------------------|
| id               | UUID (PK)     | Auto-generated UUID v4        |
| ndis_number      | VARCHAR(20)   | Unique, indexed, not null     |
| first_name       | VARCHAR(100)  | Not null                      |
| last_name        | VARCHAR(100)  | Not null                      |
| date_of_birth    | DATE          | Optional                      |
| email            | VARCHAR(255)  | Optional                      |
| phone            | VARCHAR(20)   | Optional                      |
| address          | TEXT          | Optional                      |
| is_active        | BOOLEAN       | Default true                  |
| created_at       | TIMESTAMPTZ   | Auto-set on insert            |
| updated_at       | TIMESTAMPTZ   | Auto-set on insert and update |

---

### `plans`
NDIS plans associated with a participant.

| Column           | Type          | Notes                      |
|------------------|---------------|----------------------------|
| id               | UUID (PK)     |                            |
| participant_id   | UUID (FK)     | → participants.id, indexed |
| plan_start_date  | DATE          | Not null                   |
| plan_end_date    | DATE          | Not null                   |
| total_funding    | NUMERIC(12,2) | Not null                   |
| plan_manager     | VARCHAR(255)  | Optional                   |
| is_active        | BOOLEAN       | Default true               |
| created_at       | TIMESTAMPTZ   |                            |
| updated_at       | TIMESTAMPTZ   |                            |

---

### `providers`
Service providers who submit invoices.

| Column           | Type          | Notes              |
|------------------|---------------|--------------------|
| id               | UUID (PK)     |                    |
| abn              | VARCHAR(11)   | Unique, not null   |
| name             | VARCHAR(255)  | Not null           |
| email            | VARCHAR(255)  | Optional           |
| phone            | VARCHAR(20)   | Optional           |
| address          | TEXT          | Optional           |
| bank_bsb         | VARCHAR(6)    | Optional           |
| bank_account     | VARCHAR(20)   | Optional           |
| xero_contact_id  | VARCHAR(100)  | Optional           |
| is_active        | BOOLEAN       | Default true       |
| created_at       | TIMESTAMPTZ   |                    |
| updated_at       | TIMESTAMPTZ   |                    |

---

### `users`
CRM users (staff) authenticated via Auth0.

| Column       | Type          | Notes                        |
|--------------|---------------|------------------------------|
| id           | UUID (PK)     |                              |
| auth0_id     | VARCHAR(255)  | Unique, not null             |
| email        | VARCHAR(255)  | Unique, not null             |
| first_name   | VARCHAR(100)  | Optional                     |
| last_name    | VARCHAR(100)  | Optional                     |
| role         | VARCHAR(50)   | Admin / Coordinator / Viewer |
| is_active    | BOOLEAN       | Default true                 |
| last_login   | TIMESTAMPTZ   | Optional                     |
| created_at   | TIMESTAMPTZ   |                              |
| updated_at   | TIMESTAMPTZ   |                              |

---

### `support_categories`
Budget categories within a plan (e.g. Daily Activities, Transport).

| Column                | Type          | Notes                |
|-----------------------|---------------|----------------------|
| id                    | UUID (PK)     |                      |
| plan_id               | UUID (FK)     | → plans.id, indexed  |
| ndis_support_category | VARCHAR(100)  | Not null             |
| budget_allocated      | NUMERIC(12,2) | Not null             |
| budget_spent          | NUMERIC(12,2) | Default 0            |
| budget_remaining      | NUMERIC(12,2) | Computed / optional  |
| created_at            | TIMESTAMPTZ   |                      |
| updated_at            | TIMESTAMPTZ   |                      |

---

### `email_threads`
Outlook email threads associated with invoice submissions.

| Column            | Type          | Notes                      |
|-------------------|---------------|----------------------------|
| id                | UUID (PK)     |                            |
| outlook_thread_id | VARCHAR(255)  | Unique, not null           |
| outlook_message_id| VARCHAR(255)  | Optional                   |
| subject           | VARCHAR(500)  | Optional                   |
| sender_email      | VARCHAR(255)  | Optional                   |
| received_at       | TIMESTAMPTZ   | Optional                   |
| processed         | BOOLEAN       | Default false              |
| provider_id       | UUID (FK)     | → providers.id, indexed    |
| created_at        | TIMESTAMPTZ   |                            |
| updated_at        | TIMESTAMPTZ   |                            |

---

### `invoices`
Invoices submitted by providers for participant services.

| Column           | Type          | Notes                         |
|------------------|---------------|-------------------------------|
| id               | UUID (PK)     |                               |
| participant_id   | UUID (FK)     | → participants.id, indexed    |
| provider_id      | UUID (FK)     | → providers.id, indexed       |
| plan_id          | UUID (FK)     | → plans.id, indexed           |
| invoice_number   | VARCHAR(100)  | Not null                      |
| invoice_date     | DATE          | Not null                      |
| due_date         | DATE          | Optional                      |
| total_amount     | NUMERIC(12,2) | Not null                      |
| gst_amount       | NUMERIC(12,2) | Default 0                     |
| status           | VARCHAR(50)   | pending/approved/rejected/paid|
| ocr_confidence   | NUMERIC(5,2)  | OCR extraction confidence     |
| xero_invoice_id  | VARCHAR(100)  | Optional Xero reference       |
| email_thread_id  | UUID (FK)     | → email_threads.id, indexed   |
| reviewed_by      | UUID (FK)     | → users.id                    |
| reviewed_at      | TIMESTAMPTZ   | Optional                      |
| created_at       | TIMESTAMPTZ   |                               |
| updated_at       | TIMESTAMPTZ   |                               |

---

### `invoice_line_items`
Individual line items belonging to an invoice.

| Column               | Type          | Notes                          |
|----------------------|---------------|--------------------------------|
| id                   | UUID (PK)     |                                |
| invoice_id           | UUID (FK)     | → invoices.id, indexed         |
| support_item_number  | VARCHAR(50)   | NDIS support item number       |
| description          | TEXT          | Optional                       |
| unit_price           | NUMERIC(10,2) | Not null                       |
| quantity             | NUMERIC(10,2) | Not null                       |
| total                | NUMERIC(12,2) | Not null                       |
| support_category_id  | UUID (FK)     | → support_categories.id, indexed|
| created_at           | TIMESTAMPTZ   |                                |
| updated_at           | TIMESTAMPTZ   |                                |

---

### `documents`
Files stored in Google Cloud Storage, linked to participants or invoices.

| Column            | Type          | Notes                       |
|-------------------|---------------|-----------------------------|
| id                | UUID (PK)     |                             |
| participant_id    | UUID (FK)     | → participants.id, indexed  |
| invoice_id        | UUID (FK)     | → invoices.id, indexed      |
| document_type     | VARCHAR(50)   | invoice / plan / statement  |
| gcs_bucket        | VARCHAR(255)  | GCS bucket name             |
| gcs_path          | VARCHAR(500)  | GCS object path             |
| original_filename | VARCHAR(255)  | Optional                    |
| mime_type         | VARCHAR(100)  | Optional                    |
| file_size_bytes   | INTEGER       | Optional                    |
| uploaded_by       | UUID (FK)     | → users.id                  |
| created_at        | TIMESTAMPTZ   |                             |
| updated_at        | TIMESTAMPTZ   |                             |

---

### `audit_log`
Immutable audit trail of all create/update/delete/approve actions.

| Column      | Type          | Notes                        |
|-------------|---------------|------------------------------|
| id          | UUID (PK)     |                              |
| user_id     | UUID (FK)     | → users.id, indexed          |
| action      | VARCHAR(100)  | CREATE/UPDATE/DELETE/APPROVE |
| entity_type | VARCHAR(100)  | Invoice/Participant/etc.     |
| entity_id   | UUID          | ID of the affected record    |
| old_values  | JSONB         | State before change          |
| new_values  | JSONB         | State after change           |
| ip_address  | VARCHAR(45)   | Supports IPv6                |
| created_at  | TIMESTAMPTZ   | Not null, auto-set           |

---

## Relationships

```
Participant  1──*  Plan
Plan         1──*  SupportCategory
Participant  1──*  Invoice
Provider     1──*  Invoice
Plan         1──*  Invoice
Invoice      1──*  InvoiceLineItem
SupportCategory 1──*  InvoiceLineItem
Invoice      1──*  Document
Participant  1──*  Document
Provider     1──*  EmailThread
EmailThread  1──*  Invoice
User         1──*  Invoice  (reviewed_by)
User         1──*  Document (uploaded_by)
User         1──*  AuditLog
```

## Index Strategy

- `participants.ndis_number` — unique index for fast participant lookup
- `plans.participant_id` — FK index for plan queries per participant
- `support_categories.plan_id` — FK index
- `invoices.participant_id`, `invoices.provider_id`, `invoices.plan_id`, `invoices.email_thread_id` — FK indexes for common join patterns
- `invoice_line_items.invoice_id`, `invoice_line_items.support_category_id` — FK indexes
- `documents.participant_id`, `documents.invoice_id` — FK indexes
- `email_threads.provider_id` — FK index
- `audit_log.user_id` — FK index for user audit queries

## Running Migrations

### Apply all pending migrations

```bash
cd backend
alembic upgrade head
```

### Create a new auto-generated migration

```bash
cd backend
alembic revision --autogenerate -m "description"
```

### Roll back one revision

```bash
cd backend
alembic downgrade -1
```

## Environment Variables

The database connection URL is read from the `DATABASE_URL` environment variable.

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ndis_crm
```
