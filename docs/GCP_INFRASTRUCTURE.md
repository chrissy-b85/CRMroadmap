# GCP Infrastructure

This document describes the Google Cloud Platform infrastructure for the NDIS CRM project, managed with Terraform.

## Architecture Overview

```
                        ┌─────────────────────────────────────────┐
                        │           GCP Project: ndis-crm-prod     │
                        │           Region: australia-southeast1    │
                        │                                           │
                        │  ┌──────────────┐  ┌──────────────────┐  │
                        │  │  Cloud Run   │  │   Cloud Run      │  │
           Users ──────►│  │  Frontend    │─►│   Backend        │  │
                        │  │  (Next.js    │  │   (FastAPI        │  │
                        │  │   port 3000) │  │    port 8000)    │  │
                        │  └──────────────┘  └────────┬─────────┘  │
                        │                             │             │
                        │         ┌───────────────────┼──────────┐  │
                        │         │                   │          │  │
                        │  ┌──────▼──────┐  ┌─────────▼──────┐  │  │
                        │  │  Cloud SQL  │  │  Secret Manager│  │  │
                        │  │ PostgreSQL  │  │  (credentials) │  │  │
                        │  │     15      │  └────────────────┘  │  │
                        │  └─────────────┘                      │  │
                        │         │                              │  │
                        │  ┌──────▼──────────────────────────┐  │  │
                        │  │        Cloud Storage (GCS)       │  │  │
                        │  │  invoices | documents | statements│  │  │
                        │  └─────────────────────────────────-┘  │  │
                        │         │                              │  │
                        │  ┌──────▼──────┐                      │  │
                        │  │ Document AI │                      │  │
                        │  │  Invoice    │                      │  │
                        │  │  Processor  │                      │  │
                        │  └─────────────┘                      │  │
                        └─────────────────────────────────────────┘
```

### Components

| Component | Resource | Purpose |
|---|---|---|
| **Cloud Run** | `ndis-crm-backend` | FastAPI backend API (port 8000) |
| **Cloud Run** | `ndis-crm-frontend` | Next.js frontend (port 3000) |
| **Cloud SQL** | `ndis-crm-db` (PostgreSQL 15) | Primary relational database |
| **Cloud Storage** | `ndis-crm-invoices` | Invoice PDF uploads |
| **Cloud Storage** | `ndis-crm-documents` | Participant documents |
| **Cloud Storage** | `ndis-crm-statements` | PDF statements |
| **Document AI** | `ndis-crm-invoice-parser` | Automated invoice OCR and parsing |
| **Secret Manager** | 9 secrets | Credentials and API keys |
| **IAM** | 2 service accounts | Least-privilege access for backend and frontend |

---

## Prerequisites

Before deploying the infrastructure, ensure you have:

1. **Terraform** v1.5 or later — [Install Terraform](https://developer.hashicorp.com/terraform/install)
2. **Google Cloud CLI** — [Install gcloud](https://cloud.google.com/sdk/docs/install)
3. A GCP project named `ndis-crm-prod` with **billing enabled**
4. Owner or Editor permissions on the GCP project
5. A GCS bucket named `ndis-crm-prod-tfstate` for Terraform remote state

### Create the Terraform state bucket

```bash
gcloud storage buckets create gs://ndis-crm-prod-tfstate \
  --project=ndis-crm-prod \
  --location=australia-southeast1 \
  --uniform-bucket-level-access
```

---

## Deployment Instructions

### 1. Authenticate with GCP

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project ndis-crm-prod
```

### 2. Clone the repository and navigate to the Terraform directory

```bash
cd infra/gcp
```

### 3. Copy and edit the variable values file

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set values appropriate for your deployment.

### 4. Initialise Terraform

```bash
terraform init
```

### 5. Review the execution plan

```bash
terraform plan
```

Review the output carefully to confirm the resources that will be created.

### 6. Apply the configuration

```bash
terraform apply
```

Type `yes` when prompted to confirm.

### 7. Retrieve outputs

After a successful apply, retrieve the key outputs:

```bash
terraform output backend_cloud_run_url
terraform output frontend_cloud_run_url
terraform output db_connection_name
terraform output document_ai_processor_id
```

---

## Secret Manager Setup

Terraform creates the Secret Manager secret resources, but does **not** store secret values. You must populate each secret manually after provisioning.

### Populate secrets

```bash
# Auth0
echo -n "your-tenant.au.auth0.com" | \
  gcloud secrets versions add auth0-domain --data-file=-

echo -n "https://your-api-identifier" | \
  gcloud secrets versions add auth0-audience --data-file=-

echo -n "YOUR_AUTH0_CLIENT_SECRET" | \
  gcloud secrets versions add auth0-client-secret --data-file=-

# Note: db-password is automatically generated and stored by Terraform.
# No manual step required.

# Xero
echo -n "YOUR_XERO_CLIENT_ID" | \
  gcloud secrets versions add xero-client-id --data-file=-

echo -n "YOUR_XERO_CLIENT_SECRET" | \
  gcloud secrets versions add xero-client-secret --data-file=-

# Outlook / Microsoft Graph
echo -n "YOUR_OUTLOOK_CLIENT_ID" | \
  gcloud secrets versions add outlook-client-id --data-file=-

echo -n "YOUR_OUTLOOK_CLIENT_SECRET" | \
  gcloud secrets versions add outlook-client-secret --data-file=-

# Document AI — populate after first apply to get processor ID
terraform output document_ai_processor_id | \
  gcloud secrets versions add document-ai-processor-id --data-file=-
```

---

## IAM Roles Explanation

### `ndis-crm-backend` Service Account

| Role | Purpose |
|---|---|
| `roles/cloudsql.client` | Connect to Cloud SQL instance via Cloud SQL Auth Proxy |
| `roles/storage.objectAdmin` | Read/write objects in all three GCS buckets |
| `roles/secretmanager.secretAccessor` | Access all application secrets at runtime |
| `roles/documentai.apiUser` | Call Document AI to process invoice PDFs |

### `ndis-crm-frontend` Service Account

| Role | Purpose |
|---|---|
| `roles/run.invoker` | Allow the service to invoke Cloud Run services |

The frontend service account is intentionally minimal. The frontend only serves the Next.js app and calls the backend API — it does not interact with GCP services directly.

---

## Terraform Files Reference

| File | Description |
|---|---|
| `main.tf` | Root config — Terraform settings, GCP provider, remote state backend |
| `variables.tf` | Input variables with defaults |
| `outputs.tf` | Output values exported after `terraform apply` |
| `terraform.tfvars.example` | Example variable values to copy and edit |
| `apis.tf` | Enable required GCP APIs |
| `iam.tf` | Service accounts and project-level IAM role bindings |
| `cloud_run.tf` | Cloud Run services for backend and frontend |
| `cloud_sql.tf` | Cloud SQL PostgreSQL 15 instance, database, and user |
| `storage.tf` | GCS buckets for invoices, documents, and statements |
| `document_ai.tf` | Document AI processor for invoice parsing |
| `secret_manager.tf` | Secret Manager secrets and per-secret IAM bindings |

---

## Region

All resources are deployed to **`australia-southeast1`** (Sydney), except Document AI which uses **`us`** (Document AI processors are only available in `us` and `eu` multi-regions). The backend is configured to call the Document AI endpoint with the correct regional project path.

---

## Destroying the Infrastructure

> **Warning:** This will permanently delete all resources including the Cloud SQL instance and GCS bucket contents.

```bash
# First remove deletion protection from Cloud SQL
terraform apply -var="..." # after editing deletion_protection = false in cloud_sql.tf

terraform destroy
```
