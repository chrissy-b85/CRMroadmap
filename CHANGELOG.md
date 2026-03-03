# NDIS CRM Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-03-03

### Added

#### Participant & Plan Management
- Full NDIS participant record management (create, edit, archive)
- NDIS plan management with support category budgets (Core, Capacity Building, Capital)
- Participant portal with self-service budget view and invoice approval

#### Invoice Ingestion & Processing
- Automated invoice ingestion from shared Outlook mailbox via Microsoft Graph API
- OCR-based invoice data extraction using Google Document AI
- Automated invoice validation engine (duplicate detection, ABN verification,
  budget availability check, NDIS price catalogue compliance)

#### Staff Invoice Review Dashboard
- Paginated invoice review queue with filtering and sorting
- Side-by-side PDF preview and extracted data review panel
- Approve / reject / request-changes workflow with audit trail

#### Accounting Integration
- Xero OAuth 2.0 integration for approved invoice synchronisation
- Xero webhook support for payment event notifications
- Xero reconnection and token refresh handling

#### Budget Monitoring & Alerts
- Real-time budget tracking per support category
- Budget alerts at 80 % and 100 % utilisation
- Push notifications to participant portal (Web Push / VAPID)
- Outlook email notifications via Microsoft Graph API

#### Reporting & Statements
- Staff reporting dashboard with invoice summary and budget utilisation reports
- Monthly PDF statement generation per participant
- CSV and PDF export for all reports

#### Audit & Compliance
- Comprehensive audit logging for all data changes, approvals, and rejections
- NDIS price catalogue integration and validation

#### Production Infrastructure
- Google Cloud Run services for backend (FastAPI) and frontend (Next.js)
- Cloud SQL PostgreSQL 16 with private IP, regional HA, and automated backups
- Cloud Memorystore Redis for Celery task broker
- Cloud Storage buckets for documents and database backups
- Secret Manager for all credentials
- Artifact Registry for container images
- Terraform IaC for all GCP resources (`infra/terraform/`)
- GitHub Actions CI/CD pipelines for backend and frontend deployments
- Alembic database migration workflow

#### Documentation
- Staff training guide (`docs/STAFF_TRAINING_GUIDE.md`)
- Participant portal guide (`docs/PARTICIPANT_PORTAL_GUIDE.md`)
- System administrator guide (`docs/ADMIN_GUIDE.md`)
- Technical architecture document (`docs/ARCHITECTURE.md`)
- Production go-live checklist (`docs/GO_LIVE_CHECKLIST.md`)
- Infrastructure setup guide (`infra/README.md`)
