# UAT Checklist — NDIS CRM

> **Sprint:** UAT / QA / Bugfix  
> **Environment:** Staging  
> **Tester:** ___________________  
> **Date:** ___________________

Mark each item **Pass ✅ / Fail ❌ / N/A** and add notes where relevant.

---

## Staff CRM Flows

### Authentication
| # | Test Case | Expected Result | Status | Notes |
|---|-----------|-----------------|--------|-------|
| S01 | Login via Auth0 with Coordinator role credentials | Redirect to staff dashboard; role-appropriate nav visible | | |
| S02 | Attempt login with invalid credentials | Auth0 shows error; no dashboard access | | |
| S03 | Access a protected route without a token | Redirect to login page; HTTP 401 returned by API | | |

### Participant Management
| # | Test Case | Expected Result | Status | Notes |
|---|-----------|-----------------|--------|-------|
| S04 | Create a new participant record with all required fields | Record saved; 201 response; participant appears in list | | |
| S05 | Create a participant with a duplicate NDIS number | 409 Conflict error displayed | | |
| S06 | Search for a participant by name | Matching participants listed; pagination works | | |
| S07 | View a participant's profile page | All fields, plans, and audit log visible | | |
| S08 | Edit a participant's phone/address | Changes saved; audit log entry created | | |

### NDIS Plan Management
| # | Test Case | Expected Result | Status | Notes |
|---|-----------|-----------------|--------|-------|
| S09 | Add an NDIS plan with start/end dates and total funding | Plan saved and linked to participant | | |
| S10 | Add support categories with budget allocations to a plan | Categories saved; total allocated matches sum | | |
| S11 | View budget summary for a plan | Burn rate, utilisation %, and alerts displayed correctly | | |
| S12 | Trigger budget alert at 75% utilisation | WARNING alert appears in dashboard | | |
| S13 | Trigger budget alert at 90% utilisation | CRITICAL alert appears in dashboard | | |

### Provider Management
| # | Test Case | Expected Result | Status | Notes |
|---|-----------|-----------------|--------|-------|
| S14 | Register a new provider with valid ABN | Provider saved; ABN validation passes | | |
| S15 | Register a provider with an invalid ABN | Validation error shown; record not saved | | |
| S16 | Search for a provider by name | Matching results returned | | |

### Invoice Queue
| # | Test Case | Expected Result | Status | Notes |
|---|-----------|-----------------|--------|-------|
| S17 | View the invoice queue | List loads with correct columns and status badges | | |
| S18 | Filter invoice queue by status (e.g. `pending_approval`) | Only matching invoices displayed | | |
| S19 | Search invoice queue by provider name | Matching invoices displayed | | |
| S20 | Approve an invoice with optional notes | Status changes to `approved`; `budget_spent` updated on support category | | |
| S21 | Reject an invoice with a reason | Status changes to `rejected`; rejection reason logged in audit log | | |
| S22 | Request more info on an invoice | Status changes to `info_requested`; reason recorded | | |
| S23 | View a single invoice with OCR confidence bar and line items | All fields rendered; line items displayed | | |

### Reporting & Exports
| # | Test Case | Expected Result | Status | Notes |
|---|-----------|-----------------|--------|-------|
| S24 | View staff dashboard KPIs | Totals for pending invoices, active participants, and budget alerts displayed | | |
| S25 | Run a spend-by-category report | Correct totals per category shown | | |
| S26 | Export spend report as CSV | CSV downloaded with correct headers and data | | |
| S27 | Download a participant's monthly PDF statement | PDF generated with correct data for the selected month | | |

### Audit & Correspondence
| # | Test Case | Expected Result | Status | Notes |
|---|-----------|-----------------|--------|-------|
| S28 | View audit log for a participant | All relevant actions listed with timestamp, user, before/after values | | |
| S29 | View correspondence history for a participant | Email thread history displayed chronologically | | |

---

## Participant PWA Flows

### Authentication
| # | Test Case | Expected Result | Status | Notes |
|---|-----------|-----------------|--------|-------|
| P01 | Login via Auth0 with Participant role | Redirected to participant portal; only own data visible | | |
| P02 | Attempt to access staff CRM URL as participant | 403 Forbidden returned | | |

### Budget Overview
| # | Test Case | Expected Result | Status | Notes |
|---|-----------|-----------------|--------|-------|
| P03 | View budget overview | All support categories listed with progress bars and utilisation % | | |
| P04 | Verify progress bar colour at <75% utilisation | Bar renders green | | |
| P05 | Verify progress bar colour at 75–90% utilisation | Bar renders amber/yellow | | |
| P06 | Verify progress bar colour at >90% utilisation | Bar renders red/orange | | |

### Invoice Actions
| # | Test Case | Expected Result | Status | Notes |
|---|-----------|-----------------|--------|-------|
| P07 | View list of pending invoices | Invoices with `PENDING_APPROVAL` status listed | | |
| P08 | Approve an invoice (one-tap confirmation) | Invoice marked as participant-approved; confirmation message shown | | |
| P09 | Submit a query message on an invoice | Status changes to `info_requested`; message saved | | |

### PWA Features
| # | Test Case | Expected Result | Status | Notes |
|---|-----------|-----------------|--------|-------|
| P10 | Install PWA on mobile device (Android Chrome) | Install prompt appears; app adds to home screen | | |
| P11 | Install PWA on iOS Safari | Sharing sheet → Add to Home Screen works | | |
| P12 | Receive push notification for a new invoice | Notification appears on device when new invoice requires approval | | |

---

## Admin Flows

### Integrations
| # | Test Case | Expected Result | Status | Notes |
|---|-----------|-----------------|--------|-------|
| A01 | Connect Xero integration (OAuth2 flow) | Connection saved; tenant name displayed | | |
| A02 | Trigger manual invoice validation | Validation rules run; results logged | | |
| A03 | Generate an ad-hoc PDF statement for any participant | PDF produced and downloaded | | |

### Monitoring & Exports
| # | Test Case | Expected Result | Status | Notes |
|---|-----------|-----------------|--------|-------|
| A04 | View all budget alerts across all participants | All CRITICAL and WARNING alerts listed | | |
| A05 | Export audit log as CSV | CSV downloaded with correct columns | | |

---

## Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Coordinator UAT | | | |
| Admin UAT | | | |
| Participant UAT | | | |
| QA Lead | | | |
