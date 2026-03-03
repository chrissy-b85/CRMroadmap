# Infrastructure — NDIS CRM

This directory contains the Terraform configuration for the NDIS CRM production
environment on Google Cloud Platform (GCP), targeting the `australia-southeast1`
(Sydney) region to satisfy Australian data sovereignty requirements.

## Directory layout

```
infra/
├── terraform/          # Terraform root module (all IaC lives here)
│   ├── main.tf         # Provider configuration and Terraform backend
│   ├── variables.tf    # Input variables
│   ├── outputs.tf      # Output values (URLs, connection strings, etc.)
│   ├── apis.tf         # GCP API enablement
│   ├── network.tf      # VPC, subnet, VPC Serverless Connector
│   ├── iam.tf          # Service accounts and IAM bindings
│   ├── cloud_run.tf    # Cloud Run services (backend + frontend)
│   ├── cloud_sql.tf    # Cloud SQL PostgreSQL instance
│   ├── gcs.tf          # GCS buckets (documents + backups)
│   ├── secret_manager.tf  # Secret Manager secret resources
│   └── terraform.tfvars.example  # Example variable values
└── scripts/
    ├── bootstrap.sh    # One-time GCS bucket creation for Terraform state
    └── setup-gcp.sh    # Helper to enable APIs and create initial SA
```

## Prerequisites

| Tool | Version |
|------|---------|
| [Terraform](https://developer.hashicorp.com/terraform/downloads) | ≥ 1.5 |
| [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) | latest |
| GCP project with billing enabled | — |

Authenticate the Cloud SDK before running any Terraform commands:

```bash
gcloud auth application-default login
gcloud config set project YOUR_GCP_PROJECT_ID
```

## First-time setup

### 1. Bootstrap Terraform remote state

Run the bootstrap script once to create the GCS bucket that stores Terraform state:

```bash
bash infra/scripts/bootstrap.sh
```

### 2. Initialise Terraform

```bash
cd infra/terraform
terraform init
```

### 3. Create your variable file

Copy the example and fill in your project-specific values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
project_id = "your-gcp-project-id"
region     = "australia-southeast1"
```

### 4. Review the plan

```bash
terraform plan
```

### 5. Apply

```bash
terraform apply
```

Terraform will create all GCP resources. Review the plan output carefully before
confirming with `yes`.

## Outputs

After a successful `apply`, Terraform prints the following outputs:

| Output | Description |
|--------|-------------|
| `backend_url` | Cloud Run URL for the FastAPI backend |
| `frontend_url` | Cloud Run URL for the Next.js frontend |
| `cloud_sql_connection_name` | Cloud SQL connection name (`project:region:instance`) |
| `cloud_sql_private_ip` | Private IP of the Cloud SQL instance |
| `documents_bucket_name` | GCS bucket for document storage |
| `backups_bucket_name` | GCS bucket for database backups |
| `artifact_registry_repository` | Container image repository name |

## Populating secrets

Terraform creates the Secret Manager *resources* (containers) but does **not**
store secret values (they must never be committed to version control).

After `terraform apply`, populate each secret:

```bash
echo -n "YOUR_VALUE" | gcloud secrets versions add SECRET_ID --data-file=-
```

Required secrets:

| Secret ID | Description |
|-----------|-------------|
| `database-url` | PostgreSQL asyncpg connection string |
| `redis-url` | Redis/Memorystore connection string |
| `auth0-domain` | Auth0 tenant domain |
| `auth0-audience` | Auth0 API audience |
| `auth0-client-id` | Auth0 SPA client ID |
| `auth0-client-secret` | Auth0 backend client secret |
| `xero-client-id` | Xero OAuth 2.0 client ID |
| `xero-client-secret` | Xero OAuth 2.0 client secret |
| `msgraph-client-id` | Microsoft Graph client ID |
| `msgraph-client-secret` | Microsoft Graph client secret |
| `msgraph-tenant-id` | Azure AD tenant ID |
| `document-ai-processor-id` | Google Document AI processor ID |

## Destroying infrastructure

> ⚠️ **Warning:** The Cloud SQL instance and GCS document bucket have
> `deletion_protection = true` / `force_destroy = false`. You must disable these
> flags before `terraform destroy` will succeed.

```bash
terraform destroy
```

## CI/CD deployment

Container images are built and deployed automatically on every push to `main`
via the GitHub Actions workflows in `.github/workflows/`. See
[`docs/CI-CD.md`](../docs/CI-CD.md) for details.
