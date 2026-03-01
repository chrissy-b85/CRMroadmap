# NDIS Plan Management CRM — Project Roadmap & Key Features

**Organisation:** TBC
**Repository:** chrissy-b85/CRMroadmap
**Document Version:** 1.0
**Date:** 2026-03-01
**Status:** Planning Phase

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Business Profile](#2-business-profile)
3. [Final Tech Stack](#3-final-tech-stack)
4. [System Architecture](#4-system-architecture)
5. [Key Features](#5-key-features)
6. [Database Schema Overview](#6-database-schema-overview)
7. [Development Roadmap](#7-development-roadmap)
8. [Compliance & Security](#8-compliance--security)
9. [Integrations](#9-integrations)
10. [Future Phases](#10-future-phases)

---

## 1. Project Overview

This document outlines the full roadmap and key features for a custom-built **NDIS Plan Management CRM** system. The system is designed to support a registered NDIS Plan Management provider, managing the end-to-end lifecycle of participant plans, provider invoices, budget tracking, and compliance reporting.

The system consists of:
- A **Staff Web CRM** for internal team use
- A **Participant PWA (Progressive Web App)** for participant budget viewing and invoice approval
- A **FastAPI Python backend** serving both applications
- Full integrations with **Xero**, **Microsoft Outlook**, and **Google Document AI**

---

## 2. Business Profile

| Item | Detail |
|---|---|
| **Number of Participants** | 750 |
| **Staff / CRM Users** | 4 |
| **Accounting Software** | Xero |
| **Email Platform** | Microsoft Outlook (Microsoft 365) |
| **Participant Portal** | Yes — PWA (iOS & Android installable) |
| **PRODA / PACE Claims** | Manual (Phase 1) → API Integration (Phase 3) |
| **Support Categories** | Multiple per participant |
| **AI Invoice Processing** | Google Document AI (Phase 1) |
| **Cloud Platform** | Google Cloud Platform — australia-southeast1 (Sydney) |

---

## 3. Final Tech Stack

| Layer | Technology |
|---|---|
| **Staff Web CRM (Frontend)** | Next.js + shadcn/ui + Recharts (TypeScript) |
| **Participant PWA** | Next.js PWA (installable on iOS & Android) |
| **Backend** | FastAPI (Python) |
| **ORM** | SQLAlchemy 2.0 + Alembic (migrations) |
| **Data Validation** | Pydantic v2 |
| **Database** | PostgreSQL — GCP Cloud SQL (Sydney) |
| **Authentication** | Auth0 (MFA + RBAC) |
| **File Storage** | Google Cloud Storage (Sydney) |
| **Hosting** | Google Cloud Run (Sydney) |
| **AI / OCR** | Google Document AI (Invoice Parser) |
| **Task Queue** | Celery + Redis |
| **PDF Generation** | WeasyPrint |
| **Accounting Integration** | Xero API (pyxero) |
| **Email Integration** | Microsoft Graph API (msgraph-sdk) |
| **Secrets Management** | GCP Secret Manager |
| **Testing** | Pytest (backend) + Jest (frontend) |
| **Linting & Formatting** | Ruff + Black (Python) |
| **CI/CD** | GitHub Actions → GCP Cloud Run |
| **Region** | australia-southeast1 — Sydney, Australia |

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Google Cloud Platform                       │
│              (australia-southeast1 — Sydney)                 │
│                                                              │
│  ┌─────────────────┐    ┌───────────────────────────────┐   │
│  │  Cloud Run      │    │  Cloud SQL (PostgreSQL)       │   │
│  │  FastAPI Backend│───▶│  Main CRM Database            │   │
│  └────────┬────────┘    └───────────────────────────────┘   │
│           │                                                  │
│           ▼                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Google Cloud Storage (GCS)                │  │
│  │   Plans | Invoices | Agreements | Statements | Docs    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─────────────────┐    ┌───────────────────────────────┐   │
│  │  Document AI    │    │  Celery + Redis               │   │
│  │  Invoice OCR    │    │  Background Job Queue         │   │
│  └─────────────────┘    └───────────────────────────────┘   │
│                                                              │
│  ┌─────────────────┐    ┌───────────────────────────────┐   │
│  │  Cloud CDN      │    │  Cloud Armor (WAF/DDoS)       │   │
│  └─────────────────┘    └───────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
            │                          │
            ▼                          ▼
   ┌─────────────────┐       ┌──────────────────────┐
   │  Staff Web CRM  │       │  Participant PWA      │
   │  Next.js        │       │  Next.js (PWA)        │
   │  (4 staff users)│       │  iOS + Android        │
   └─────────────────┘       └──────────────────────┘
            │                          │
   ┌────────┴──────────────────────────┴──────────┐
   │              External Integrations            │
   │  Xero API  |  Microsoft Graph  |  NDIS Price  │
   │  (Accounting) (Outlook Email)   Guide API     │
   └───────────────────────────────────────────────┘
```

---

## 5. Key Features

### 5.1 Participant Management
- Full participant profiles (name, NDIS number, DOB, contact details)
- Nominee / guardian contact management
- Link to active and historical NDIS plans
- Multiple support categories per plan
- Status tracking (Active, Inactive, Plan Review Pending)
- Document storage (plans, service agreements, ID documents)
- Full audit trail of all participant record changes

### 5.2 Plan & Budget Management
- Create and manage NDIS plans per participant
- Multiple support categories per plan (Daily Activities, Capacity Building, Transport, etc.)
- Allocated budget per support category
- Real-time spend tracking — auto-updated on invoice approval
- Remaining budget calculations and visual progress indicators
- Low budget threshold alerts (configurable per participant)
- Plan expiry alerts (30, 14, 7 days prior)
- Historical plan comparisons

### 5.3 Invoice Processing (AI-Powered)
- Automated invoice ingestion from Outlook shared inbox via Microsoft Graph API
- PDF invoices automatically stored in Google Cloud Storage
- **Google Document AI** extracts:
  - Provider name & ABN
  - Invoice number & date
  - Participant name & NDIS number
  - Line items (support item numbers, descriptions, quantities, unit prices)
  - Totals and GST
  - Confidence score per extraction
- Automated validation rules:
  - Provider ABN match
  - NDIS support item number validation against Price Guide
  - Unit price check (must not exceed NDIS Price Guide maximum)
  - Budget availability check
  - GST compliance check (NDIS services are GST-free)
  - Duplicate invoice detection
  - Active plan date range check
  - Confidence score threshold (< 85% flagged for manual review)
- Invoice status workflow: `RECEIVED → PROCESSING → VALIDATED → PENDING_APPROVAL → APPROVED → PAID`
- Failed validation invoices flagged for staff review with reason codes
- Staff override capability

### 5.4 Invoice Approval (Participant PWA)
- Push notification sent to participant when invoice awaiting approval
- Participant views invoice details and PDF in PWA
- One-tap Approve ✅ or Query ❓
- Query triggers notification to assigned staff coordinator
- Approved invoices automatically pushed to Xero

### 5.5 Provider Management
- Provider directory with full profile (business name, ABN, registration group, contact)
- Bank details (BSB + account) stored securely for payment processing
- NDIS registration group tracking
- Service agreement management and expiry alerts
- Invoice history per provider
- Provider status (Active, Inactive, Suspended)

### 5.6 Xero Integration
- Approved invoices automatically created in Xero
- Payment status synced back to CRM
- Reconciliation support
- GST handling (NDIS = GST-free)
- Xero contact auto-created for new providers
- Financial reporting via Xero data

### 5.7 Microsoft Outlook Email Integration
- Connect CRM to shared Outlook mailbox via Microsoft Graph API
- Incoming emails from participants and providers auto-linked to their CRM record
- Outgoing emails sent via Outlook (not generic no-reply)
- Full email thread history on each participant and provider profile
- Pre-built email templates:
  - Monthly statement delivery
  - Low budget alert
  - Plan expiry reminder (30/14/7 days)
  - Invoice processed confirmation
  - Invoice queried notification
  - New document uploaded
  - Welcome / onboarding email
- Automated email triggers based on system events
- Outlook calendar integration for plan review dates

### 5.8 Document Management
- Centralised document storage via Google Cloud Storage (Sydney)
- Document types: NDIS Plans, Service Agreements, Invoices, Statements, Identity Documents
- Secure access via time-limited signed URLs (no public access)
- Role-based document access controls
- Document versioning
- Upload, view, and download from staff CRM and participant PWA
- Object versioning enabled (recover deleted documents)
- All file access logged via GCP Audit Logs

### 5.9 Reporting & Compliance
- Participant plan utilisation reports
- Support category spend reports
- Invoice processing reports (volumes, processing times, AI confidence stats)
- Provider payment reports
- Financial reconciliation reports
- Compliance audit trail (every action logged with user, timestamp, IP)
- Exportable reports (PDF via WeasyPrint, CSV)
- Monthly participant statements (auto-generated PDF, delivered via Outlook)
- NDIS audit-ready data exports

### 5.10 User & Role Management
- 4 staff user accounts
- Role-based access control (RBAC) via Auth0:
  - **Admin** — Full access, user management, system configuration
  - **Coordinator** — Participant, invoice, provider management
  - **Viewer** — Read-only access to reports and records
- Multi-factor authentication (MFA) enforced for all staff
- Session management and activity logging
- Last login tracking

### 5.11 Participant PWA (Progressive Web App)
- Installable on iPhone (iOS 16.4+) and Android from browser
- Secure login via Auth0
- **Budget View:**
  - Support categories with visual progress bars
  - Allocated vs spent vs remaining
  - Low budget alerts
- **Invoice Approval:**
  - Pending invoices list
  - Invoice detail view with PDF
  - One-tap approve or query
- Push notifications (new invoices, low budget alerts)
- WCAG 2.1 AA accessibility compliant
- Responsive design (phone, tablet, desktop)

---

## 6. Database Schema Overview

### Core Tables

| Table | Description |
|---|---|
| `participants` | Participant profiles, contact details, status |
| `plans` | NDIS plans linked to participants |
| `support_categories` | Support categories per plan with budgets |
| `providers` | Provider directory with ABN, bank details |
| `invoices` | Invoice records with AI extraction data and status |
| `invoice_line_items` | Individual line items per invoice |
| `invoice_validations` | Validation check results per invoice |
| `documents` | Document metadata with GCS file paths |
| `users` | Staff user accounts with roles |
| `email_threads` | Email history linked to participants/providers |
| `email_templates` | Reusable email templates |
| `audit_log` | Complete audit trail of all system actions |

---

## 7. Development Roadmap

### Phase 1 — Full MVP (Estimated: 16–20 weeks)

#### Sprint 1–2: Foundation (Weeks 1–4)
- [ ] Repository setup and monorepo structure
- [ ] GCP project configuration (Cloud Run, Cloud SQL, GCS, Document AI)
- [ ] Auth0 configuration (staff roles, MFA, participant login)
- [ ] CI/CD pipeline (GitHub Actions → GCP Cloud Run)
- [ ] PostgreSQL schema design and Alembic migrations
- [ ] FastAPI project scaffold with core middleware
- [ ] Next.js project scaffold with shadcn/ui
- [ ] GCP Secret Manager configuration
- [ ] Local development environment (Docker Compose)

#### Sprint 3–4: Participant & Plan Management (Weeks 5–8)
- [ ] Participant CRUD (create, read, update, deactivate)
- [ ] NDIS plan management (create, edit, close)
- [ ] Support category management per plan
- [ ] Budget allocation per support category
- [ ] Participant search, filter, and pagination
- [ ] Staff CRM — participant list and detail screens
- [ ] Document upload and management (GCS integration)

#### Sprint 5–6: Provider Management & Invoice Ingestion (Weeks 9–12)
- [ ] Provider directory CRUD
- [ ] Microsoft Graph API integration (Outlook inbox monitoring)
- [ ] Invoice email ingestion pipeline
- [ ] Google Document AI integration (Invoice Parser)
- [ ] Celery + Redis task queue for async processing
- [ ] Invoice extraction and data mapping
- [ ] Invoice validation rule engine
- [ ] Invoice status workflow

#### Sprint 7–8: Budget Tracking & Xero Integration (Weeks 13–14)
- [ ] Real-time budget tracking (auto-update on invoice approval)
- [ ] Budget remaining calculations per support category
- [ ] Low budget threshold alerts
- [ ] Xero OAuth 2.0 integration
- [ ] Push approved invoices to Xero
- [ ] Payment status sync from Xero
- [ ] Provider payment processing

#### Sprint 9–10: Participant PWA (Weeks 15–16)
- [ ] Participant authentication (Auth0)
- [ ] Budget view screens (support categories + progress bars)
- [ ] Invoice approval screens (pending list, detail, PDF view)
- [ ] One-tap approve / query functionality
- [ ] Push notifications (Web Push API)
- [ ] PWA manifest and service worker (installable)
- [ ] WCAG 2.1 AA accessibility review

#### Sprint 11–12: Email Templates & Reporting (Weeks 17–18)
- [ ] Email template system (Microsoft Graph API)
- [ ] Automated email triggers (low budget, plan expiry, invoice processed)
- [ ] Monthly statement generation (WeasyPrint PDF)
- [ ] Automated statement delivery via Outlook
- [ ] Staff reporting dashboard
- [ ] Plan utilisation reports
- [ ] Invoice processing reports
- [ ] Compliance audit trail reports
- [ ] CSV and PDF export

#### Sprint 13–14: Testing, Security & Launch (Weeks 19–20)
- [ ] Full Pytest test suite (backend)
- [ ] Jest test suite (frontend)
- [ ] Security audit and penetration testing
- [ ] Performance testing (750 participants load test)
- [ ] WCAG 2.1 AA accessibility audit
- [ ] Staff user acceptance testing (UAT)
- [ ] Participant portal UAT
- [ ] Production deployment to GCP
- [ ] Staff training and onboarding documentation
- [ ] Go-live

---

### Phase 2 — Enhancements (Post-MVP)

| Feature | Description |
|---|---|
| PRODA / PACE API Integration | Direct NDIA claims lodgement (replacing manual process) |
| Bulk Invoice Upload | Manual bulk upload for non-email invoices |
| Advanced Reporting | BI dashboards, trend analysis, forecasting |
| SMS Notifications | SMS alerts for participants (low budget, invoice approval) |
| Participant Mobile App | Native Expo React Native app (iOS + Android App Store) |
| Document AI Fine-tuning | Train custom Document AI model on NDIS-specific invoice formats |

### Phase 3 — Advanced (Future)

| Feature | Description |
|---|---|
| PRODA / PACE Live API | Real-time claim submission and response handling |
| AI Invoice Anomaly Detection | ML model to flag unusual invoices or potential fraud |
| Participant Goals Tracking | Track progress toward NDIS plan goals |
| Provider Portal | Separate login for providers to submit invoices directly |
| Multi-tenant Architecture | Support multiple plan management organisations |

---

## 8. Compliance & Security

| Requirement | Implementation |
|---|---|
| **Australian Data Sovereignty** | All GCP services in australia-southeast1 (Sydney) |
| **Australian Privacy Act (APPs)** | Data handling policies, consent management, breach reporting |
| **NDIS Practice Standards** | Audit trails, compliance document tracking |
| **NDIS Quality & Safeguards** | Role-based access, incident logging |
| **Encryption at Rest** | AES-256 via GCP (Cloud SQL + GCS) |
| **Encryption in Transit** | TLS 1.3 enforced |
| **Multi-Factor Authentication** | Auth0 MFA enforced for all 4 staff users |
| **Role-Based Access Control** | Admin / Coordinator / Viewer roles |
| **Audit Trail** | Every data change logged (user, action, timestamp, IP, old/new values) |
| **Document Security** | GCS signed URLs (time-limited), no public bucket access |
| **Secret Management** | GCP Secret Manager (no secrets in code) |
| **WCAG 2.1 AA** | Accessibility compliance for participant PWA |
| **Session Management** | Auth0 session expiry, refresh token rotation |
| **DDoS Protection** | Google Cloud Armor (WAF) |

---

## 9. Integrations

### 9.1 Xero (Accounting)
- **Protocol:** OAuth 2.0
- **Library:** pyxero
- **Functions:** Create invoices, sync payment status, manage contacts, reconciliation
- **Trigger:** Participant or staff approves invoice in CRM

### 9.2 Microsoft Graph API (Outlook Email)
- **Protocol:** OAuth 2.0
- **Library:** msgraph-sdk (Python)
- **Functions:** Monitor shared inbox, send emails via Outlook, log email threads, calendar sync
- **Shared Mailbox:** Configurable (e.g. admin@yourcompany.com.au)

### 9.3 Google Document AI
- **Processor:** Invoice Parser
- **Library:** google-cloud-documentai (Python)
- **Functions:** OCR and structured data extraction from PDF invoices
- **Confidence Threshold:** 85% (below = flagged for manual review)
- **Fallback:** Document OCR processor for non-standard formats

### 9.4 NDIS Price Guide API
- **Protocol:** REST
- **Functions:** Validate support item numbers, check maximum unit prices
- **Update Frequency:** Auto-sync when NDIA publishes new Price Guide

### 9.5 PRODA / PACE (Phase 3)
- **Protocol:** NDIA REST API
- **Functions:** Direct claims lodgement, real-time claim status, payment reconciliation

---

## 10. Future Phases

```
Phase 1 (MVP) ──────────────────── Weeks 1–20
  Full CRM + AI Invoice Processing + PWA + Xero + Outlook

Phase 2 (Enhancements) ─────────── Post-MVP
  PRODA API + SMS + Advanced Reporting + Mobile App

Phase 3 (Advanced) ─────────────── Future
  AI Anomaly Detection + Provider Portal + Multi-tenant

Phase 4 (Scale) ────────────────── Future
  White-label + API marketplace + Predictive analytics
```

---

## Document History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-03-01 | chrissy-b85 | Initial roadmap document |

---

*This document is maintained in the [chrissy-b85/CRMroadmap](https://github.com/chrissy-b85/CRMroadmap) repository.*