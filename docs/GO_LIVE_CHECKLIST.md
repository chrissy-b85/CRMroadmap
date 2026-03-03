# Go-Live Checklist — NDIS CRM v1.0.0

Use this checklist to verify all steps are complete before going live.
Check each item off as it is completed.

---

## Infrastructure

- [ ] GCP project created and billing enabled
- [ ] Terraform state GCS bucket created (`bash infra/scripts/bootstrap.sh`)
- [ ] `terraform init` completed successfully
- [ ] `terraform plan` reviewed and approved
- [ ] `terraform apply` completed successfully with no errors
- [ ] Cloud Run backend service is running and healthy (`/health` returns 200)
- [ ] Cloud Run frontend service is running and serving the home page
- [ ] Cloud SQL instance is in `RUNNABLE` state
- [ ] Cloud SQL private IP is reachable from Cloud Run via VPC connector
- [ ] Cloud Memorystore Redis instance is in `READY` state
- [ ] GCS documents bucket created with correct permissions
- [ ] GCS backups bucket created with correct permissions
- [ ] Artifact Registry repository created and accessible

---

## Configuration

- [ ] All secrets loaded into Secret Manager (see `infra/README.md`)
  - [ ] `database-url`
  - [ ] `redis-url`
  - [ ] `auth0-domain`
  - [ ] `auth0-audience`
  - [ ] `auth0-client-id`
  - [ ] `auth0-client-secret`
  - [ ] `xero-client-id`
  - [ ] `xero-client-secret`
  - [ ] `msgraph-client-id`
  - [ ] `msgraph-client-secret`
  - [ ] `msgraph-tenant-id`
  - [ ] `document-ai-processor-id`
- [ ] Auth0 production application configured
  - [ ] Allowed callback URLs include production frontend URL
  - [ ] Allowed logout URLs include production frontend URL
  - [ ] Allowed web origins include production frontend URL
  - [ ] `staff` and `participant` roles created
  - [ ] MFA enforcement Action enabled for `staff` role
- [ ] DNS A/CNAME records configured for frontend and API domains
- [ ] SSL certificates valid (Cloud Run auto-manages TLS)
- [ ] CORS configured for production domain in backend settings
- [ ] Xero production app connected and OAuth token stored
- [ ] Microsoft Graph production app registered and admin consent granted
- [ ] Outlook shared mailbox (`invoices@`) accessible by the Graph app
- [ ] Document AI processor created and processor ID stored in Secret Manager

---

## CI/CD

- [ ] GitHub repository secrets configured:
  - [ ] `GCP_PROJECT_ID`
  - [ ] `GCP_WORKLOAD_IDENTITY_PROVIDER`
  - [ ] `GCP_SERVICE_ACCOUNT`
  - [ ] `CLOUD_RUN_REGION`
- [ ] `deploy-backend.yml` workflow runs successfully on push to `main`
- [ ] `deploy-frontend.yml` workflow runs successfully on push to `main`
- [ ] `run-migrations.yml` workflow is available for manual execution

---

## Data & Testing

- [ ] Database migrations run successfully (`alembic upgrade head`)
- [ ] NDIS price catalogue loaded / seeded
- [ ] Sample participants and plans created for smoke testing
- [ ] End-to-end smoke test passed:
  - [ ] Staff can log in
  - [ ] Participant can log in via portal
  - [ ] Test invoice email received and processed by OCR
  - [ ] Invoice appears in staff review queue
  - [ ] Staff can approve the invoice
  - [ ] Approved invoice syncs to Xero
  - [ ] Budget is updated after approval
  - [ ] Budget alert notification sent when threshold is reached
  - [ ] Monthly PDF statement generated successfully
- [ ] Push notifications working in participant portal (desktop + mobile)
- [ ] PWA install prompt working on iOS Safari and Android Chrome

---

## Security

- [ ] Cloud SQL has no public IP address
- [ ] Redis has no public IP address
- [ ] GCS buckets have public access prevention enforced
- [ ] All secrets are in Secret Manager (none hard-coded or in `.env` files)
- [ ] Container images are from a trusted registry (Artifact Registry)
- [ ] Auth0 anomaly detection and brute force protection enabled
- [ ] Cloud Audit Logs enabled for all services

---

## People

- [ ] Staff accounts created in Auth0 with `staff` role
- [ ] Admin accounts created in Auth0 with `admin` role
- [ ] Participant accounts created and portal invitations sent
- [ ] Staff training session completed (or training guide distributed)
- [ ] Support contact documented and communicated to all users
- [ ] On-call rotation or escalation path documented

---

## Post Go-Live

- [ ] Monitor Cloud Run error rates for 24 hours after launch
- [ ] Confirm first automated Outlook mailbox poll succeeds
- [ ] Confirm first automated Xero sync succeeds
- [ ] Confirm automated daily Cloud SQL backup runs
- [ ] Hypercare period completed (typically 2 weeks)
- [ ] Decommission any staging resources no longer needed
