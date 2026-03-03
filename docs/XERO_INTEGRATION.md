# Xero Integration

This document describes how to configure and use the Xero accounting integration with the NDIS CRM.

## Overview

The integration provides a two-way sync between the CRM and Xero:

1. **CRM → Xero**: When a CRM invoice is approved, it is automatically pushed to Xero as an Accounts Payable Bill.
2. **Xero → CRM**: When Xero marks a bill as paid (via webhook or daily reconciliation), the CRM invoice status is updated to `PAID`.

---

## Xero App Setup

### Create an OAuth 2.0 App

1. Log in to the [Xero Developer Portal](https://developer.xero.com/app/manage).
2. Click **New App**.
3. Set the app type to **Web App**.
4. Set the **Redirect URI** to match `XERO_REDIRECT_URI` in your environment (e.g. `https://your-domain.com/api/v1/xero/callback`).
5. Note the **Client ID** and **Client Secret**.

### Required Scopes

The app requires the following OAuth 2.0 scopes:

| Scope | Purpose |
|-------|---------|
| `offline_access` | Enables token refresh |
| `accounting.transactions` | Create and read invoices/bills |
| `accounting.contacts` | Create and read contacts (providers) |

---

## Environment Variables

Add the following to `backend/.env`:

```
XERO_CLIENT_ID=<your-client-id>
XERO_CLIENT_SECRET=<your-client-secret>
XERO_REDIRECT_URI=https://your-domain.com/api/v1/xero/callback
XERO_WEBHOOK_KEY=<webhook-signing-key-from-xero>
```

---

## Connecting Xero to the CRM

1. Log in to the CRM as an **Admin**.
2. Call `GET /api/v1/xero/connect` — the response includes an `auth_url`.
3. Navigate to the `auth_url` in your browser and authorise the CRM app in Xero.
4. Xero will redirect back to `/api/v1/xero/callback` with the authorisation code.
5. The CRM exchanges the code for access/refresh tokens and stores them in the `xero_connections` table.
6. Verify the connection with `GET /api/v1/xero/status`.

To disconnect: `DELETE /api/v1/xero/disconnect` (Admin only).

---

## Webhook Setup

Webhooks allow Xero to notify the CRM in real time when a bill is paid.

### Configure in Xero Developer Portal

1. In your Xero app, go to **Webhooks**.
2. Add a new webhook with the URL: `https://your-domain.com/api/v1/webhooks/xero`
3. Select the event types:
   - **Invoices** → `InvoiceUpdated`
   - **Payments** → `PaymentCreated`
4. After saving, Xero will display the **Webhook Signing Key** — copy this into `XERO_WEBHOOK_KEY`.

### Signature Validation

Every webhook request from Xero includes an `x-xero-signature` header containing an HMAC-SHA256 signature of the request body, encoded in Base64. The CRM validates this signature before processing events using the `XERO_WEBHOOK_KEY`.

### Intent to Receive

Xero sends an empty POST to your webhook URL to verify it is reachable. The CRM responds with `200 OK` for empty payloads.

---

## Account Code Mapping

NDIS support categories are mapped to Xero account codes in `backend/app/services/xero_sync_service.py`. Update the `ACCOUNT_CODE_MAP` dictionary to match your Xero chart of accounts:

```python
ACCOUNT_CODE_MAP = {
    "Support Coordination": "400",
    "Daily Activities":      "401",
    "Social Community":      "402",
    "Capacity Building":     "403",
    "Capital Supports":      "404",
}
DEFAULT_ACCOUNT_CODE = "200"
```

Ensure these account codes exist in your Xero organisation under **Accounting → Chart of Accounts**.

---

## Daily Reconciliation

In addition to real-time webhooks, a Celery beat task runs daily at 02:00 to poll Xero for any bills that have been paid but not yet reflected in the CRM:

```
reconcile-xero-payments-daily  →  app.worker.tasks.reconcile_xero_payments
```

This handles edge cases where webhooks are missed or delayed.

---

## Invoice Sync Flow

```
CRM Invoice APPROVED
        │
        ▼
sync_approved_invoice_to_xero()
  1. Load active XeroConnection (refresh token if expired)
  2. Get/create Xero Contact for provider (matched by ABN)
  3. Map line items to Xero account codes
  4. POST /Invoices → Xero creates Bill (ACCPAY, SUBMITTED)
  5. Store xero_invoice_id on CRM Invoice
  6. Write AuditLog entry
        │
        ▼
Xero Bill PAID
        │
        ▼
Webhook POST /api/v1/webhooks/xero  (or daily reconcile)
  1. Validate HMAC-SHA256 signature
  2. Handle PaymentCreated / InvoiceUpdated event
  3. sync_payment_from_xero() → update CRM status to PAID
  4. Write AuditLog entry
```
