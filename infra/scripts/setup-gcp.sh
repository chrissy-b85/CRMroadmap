#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# setup-gcp.sh — Quick-start GCP resource setup via gcloud CLI.
#
# This script is an alternative to Terraform for operators who prefer to
# configure GCP resources using gcloud commands directly.
#
# It idempotently creates all resources required for the ndis-crm-prod project:
#   - Enable required GCP APIs
#   - VPC network and subnet
#   - Service accounts with IAM roles
#   - Artifact Registry repository
#   - Cloud SQL PostgreSQL instance (private IP)
#   - GCS buckets (documents, backups)
#   - Cloud Run services (backend, frontend)
#   - Secret Manager secrets
#   - Document AI Invoice Parser processor
#
# Prerequisites:
#   - gcloud CLI installed and authenticated (gcloud auth login)
#   - Project ndis-crm-prod already created in GCP Console
#
# Usage:
#   chmod +x infra/scripts/setup-gcp.sh
#   ./infra/scripts/setup-gcp.sh
# ---------------------------------------------------------------------------
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ID="ndis-crm-prod"
REGION="australia-southeast1"
ZONE="${REGION}-a"

# Network
VPC_NAME="ndis-crm-vpc"
SUBNET_NAME="ndis-crm-subnet"
SUBNET_CIDR="10.0.0.0/24"
CONNECTOR_CIDR="10.8.0.0/28"
CONNECTOR_NAME="ndis-crm-connector"

# Service accounts
BACKEND_SA="ndis-crm-backend"
DEPLOY_SA="ndis-crm-deploy"

# Cloud SQL
SQL_INSTANCE="ndis-crm-postgres"
DB_NAME="ndis_crm"
DB_USER="ndis_crm_app"

# GCS buckets
DOCUMENTS_BUCKET="${PROJECT_ID}-documents"
BACKUPS_BUCKET="${PROJECT_ID}-backups"

# Cloud Run
BACKEND_SERVICE="ndis-crm-backend"
FRONTEND_SERVICE="ndis-crm-frontend"
BACKEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/ndis-crm/backend:latest"
FRONTEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/ndis-crm/frontend:latest"

# Artifact Registry
AR_REPO="ndis-crm"

echo "==> Setting active project..."
gcloud config set project "${PROJECT_ID}"

# ---------------------------------------------------------------------------
# 1. Enable required APIs
# ---------------------------------------------------------------------------
echo "==> Enabling required GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  documentai.googleapis.com \
  secretmanager.googleapis.com \
  vpcaccess.googleapis.com \
  servicenetworking.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  redis.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com

echo "    APIs enabled."

# ---------------------------------------------------------------------------
# 2. VPC Network and Subnet
# ---------------------------------------------------------------------------
echo "==> Creating VPC network..."
if ! gcloud compute networks describe "${VPC_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
  gcloud compute networks create "${VPC_NAME}" \
    --project="${PROJECT_ID}" \
    --subnet-mode=custom
fi

echo "==> Creating subnet..."
if ! gcloud compute networks subnets describe "${SUBNET_NAME}" \
    --region="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
  gcloud compute networks subnets create "${SUBNET_NAME}" \
    --project="${PROJECT_ID}" \
    --network="${VPC_NAME}" \
    --region="${REGION}" \
    --range="${SUBNET_CIDR}" \
    --enable-private-ip-google-access
fi

# ---------------------------------------------------------------------------
# 3. Private services access (for Cloud SQL private IP)
# ---------------------------------------------------------------------------
echo "==> Configuring private services access..."
if ! gcloud compute addresses describe google-managed-services-"${VPC_NAME}" \
    --global --project="${PROJECT_ID}" &>/dev/null; then
  gcloud compute addresses create "google-managed-services-${VPC_NAME}" \
    --project="${PROJECT_ID}" \
    --global \
    --purpose=VPC_PEERING \
    --prefix-length=16 \
    --network="${VPC_NAME}"
fi

gcloud services vpc-peerings connect \
  --project="${PROJECT_ID}" \
  --service=servicenetworking.googleapis.com \
  --ranges="google-managed-services-${VPC_NAME}" \
  --network="${VPC_NAME}" || true

# ---------------------------------------------------------------------------
# 4. VPC Serverless Connector
# ---------------------------------------------------------------------------
echo "==> Creating VPC Serverless Connector..."
if ! gcloud compute networks vpc-access connectors describe "${CONNECTOR_NAME}" \
    --region="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
  gcloud compute networks vpc-access connectors create "${CONNECTOR_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --network="${VPC_NAME}" \
    --range="${CONNECTOR_CIDR}" \
    --min-instances=2 \
    --max-instances=3 \
    --machine-type=e2-micro
fi

# ---------------------------------------------------------------------------
# 5. Service Accounts and IAM
# ---------------------------------------------------------------------------
echo "==> Creating service accounts..."

# Backend service account
if ! gcloud iam service-accounts describe \
    "${BACKEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --project="${PROJECT_ID}" &>/dev/null; then
  gcloud iam service-accounts create "${BACKEND_SA}" \
    --project="${PROJECT_ID}" \
    --display-name="NDIS CRM Backend (Cloud Run)"
fi

# Frontend service account
FRONTEND_SA="ndis-crm-frontend"
if ! gcloud iam service-accounts describe \
    "${FRONTEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --project="${PROJECT_ID}" &>/dev/null; then
  gcloud iam service-accounts create "${FRONTEND_SA}" \
    --project="${PROJECT_ID}" \
    --display-name="NDIS CRM Frontend (Cloud Run)"
fi

# Deploy service account (CI/CD)
if ! gcloud iam service-accounts describe \
    "${DEPLOY_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --project="${PROJECT_ID}" &>/dev/null; then
  gcloud iam service-accounts create "${DEPLOY_SA}" \
    --project="${PROJECT_ID}" \
    --display-name="NDIS CRM CI/CD Deploy (GitHub Actions)"
fi

echo "==> Assigning IAM roles to backend service account..."
BACKEND_SA_EMAIL="${BACKEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${BACKEND_SA_EMAIL}" \
  --role="roles/cloudsql.client" \
  --condition=None

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${BACKEND_SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${BACKEND_SA_EMAIL}" \
  --role="roles/documentai.apiUser" \
  --condition=None

echo "==> Assigning IAM roles to deploy service account..."
DEPLOY_SA_EMAIL="${DEPLOY_SA}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${DEPLOY_SA_EMAIL}" \
  --role="roles/run.developer" \
  --condition=None

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${DEPLOY_SA_EMAIL}" \
  --role="roles/artifactregistry.writer" \
  --condition=None

gcloud iam service-accounts add-iam-policy-binding "${BACKEND_SA_EMAIL}" \
  --project="${PROJECT_ID}" \
  --member="serviceAccount:${DEPLOY_SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"

# ---------------------------------------------------------------------------
# 6. Artifact Registry
# ---------------------------------------------------------------------------
echo "==> Creating Artifact Registry repository..."
if ! gcloud artifacts repositories describe "${AR_REPO}" \
    --location="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
  gcloud artifacts repositories create "${AR_REPO}" \
    --project="${PROJECT_ID}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Container images for the NDIS CRM application"
fi

# ---------------------------------------------------------------------------
# 7. Cloud SQL PostgreSQL
# ---------------------------------------------------------------------------
echo "==> Creating Cloud SQL instance (this may take several minutes)..."
if ! gcloud sql instances describe "${SQL_INSTANCE}" \
    --project="${PROJECT_ID}" &>/dev/null; then
  gcloud sql instances create "${SQL_INSTANCE}" \
    --project="${PROJECT_ID}" \
    --database-version=POSTGRES_15 \
    --region="${REGION}" \
    --tier=db-g1-small \
    --availability-type=REGIONAL \
    --no-assign-ip \
    --network="projects/${PROJECT_ID}/global/networks/${VPC_NAME}" \
    --storage-type=SSD \
    --storage-size=20 \
    --storage-auto-increase \
    --backup-start-time=02:00 \
    --enable-point-in-time-recovery \
    --retained-backups-count=30 \
    --retained-transaction-log-days=7 \
    --deletion-protection \
    --insights-config-query-insights-enabled \
    --database-flags=log_connections=on,log_disconnections=on,log_checkpoints=on,log_lock_waits=on
fi

echo "==> Creating database and user..."
gcloud sql databases create "${DB_NAME}" \
  --instance="${SQL_INSTANCE}" \
  --project="${PROJECT_ID}" || true

DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql users create "${DB_USER}" \
  --instance="${SQL_INSTANCE}" \
  --project="${PROJECT_ID}" \
  --password="${DB_PASSWORD}" || true

# Store the password directly in Secret Manager — never printed to stdout
echo -n "${DB_PASSWORD}" | gcloud secrets versions add "database-url" \
  --project="${PROJECT_ID}" \
  --data-file=- 2>/dev/null || \
  echo "    NOTE: Manually populate the database-url secret with the DB password." \
  "Run: echo -n 'postgresql+asyncpg://${DB_USER}:PASSWORD@PRIVATE_IP/${DB_NAME}' | gcloud secrets versions add database-url --data-file=-"
unset DB_PASSWORD

# ---------------------------------------------------------------------------
# 8. GCS Buckets
# ---------------------------------------------------------------------------
echo "==> Creating GCS buckets..."

# Documents bucket
if ! gsutil ls -b "gs://${DOCUMENTS_BUCKET}" &>/dev/null; then
  gsutil mb -p "${PROJECT_ID}" -l "${REGION}" -b on "gs://${DOCUMENTS_BUCKET}"
  gsutil versioning set on "gs://${DOCUMENTS_BUCKET}"
  gsutil pap set enforced "gs://${DOCUMENTS_BUCKET}"
  echo "    Created documents bucket: gs://${DOCUMENTS_BUCKET}"
fi

# GCS Object Admin for backend SA on documents bucket
gsutil iam ch \
  "serviceAccount:${BACKEND_SA_EMAIL}:roles/storage.objectAdmin" \
  "gs://${DOCUMENTS_BUCKET}"

# Backups bucket
if ! gsutil ls -b "gs://${BACKUPS_BUCKET}" &>/dev/null; then
  gsutil mb -p "${PROJECT_ID}" -l "${REGION}" \
    -c NEARLINE -b on "gs://${BACKUPS_BUCKET}"
  gsutil pap set enforced "gs://${BACKUPS_BUCKET}"
  echo "    Created backups bucket: gs://${BACKUPS_BUCKET}"
fi

# ---------------------------------------------------------------------------
# 9. Secret Manager secrets
# ---------------------------------------------------------------------------
echo "==> Creating Secret Manager secrets..."
SECRETS=(
  "database-url"
  "redis-url"
  "auth0-domain"
  "auth0-audience"
  "auth0-client-id"
  "auth0-client-secret"
  "xero-client-id"
  "xero-client-secret"
  "msgraph-client-id"
  "msgraph-client-secret"
  "msgraph-tenant-id"
  "document-ai-processor-id"
)

for SECRET in "${SECRETS[@]}"; do
  if ! gcloud secrets describe "${SECRET}" \
      --project="${PROJECT_ID}" &>/dev/null; then
    gcloud secrets create "${SECRET}" \
      --project="${PROJECT_ID}" \
      --replication-policy=user-managed \
      --locations="${REGION}" \
      --labels="environment=prod,project=ndis-crm"
    echo "    Created secret: ${SECRET}"
  else
    echo "    Secret already exists: ${SECRET}"
  fi
done

echo ""
echo "==> Populate secrets with actual values using:"
echo "    echo -n 'VALUE' | gcloud secrets versions add SECRET_ID --data-file=-"
echo ""

# ---------------------------------------------------------------------------
# 10. Document AI — Invoice Parser
# ---------------------------------------------------------------------------
echo "==> Creating Document AI Invoice Parser processor..."
PROCESSOR_RESPONSE=$(curl -s -X POST \
  "https://documentai.googleapis.com/v1/projects/${PROJECT_ID}/locations/us/processors" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "INVOICE_PROCESSOR",
    "displayName": "NDIS CRM Invoice Parser"
  }')

PROCESSOR_ID=$(echo "${PROCESSOR_RESPONSE}" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('name','').split('/')[-1])" 2>/dev/null || true)

if [ -n "${PROCESSOR_ID}" ]; then
  echo "    Document AI processor created: ${PROCESSOR_ID}"
  echo -n "${PROCESSOR_ID}" | gcloud secrets versions add "document-ai-processor-id" \
    --project="${PROJECT_ID}" --data-file=-
  echo "    Processor ID stored in Secret Manager."
else
  echo "    WARNING: Could not create Document AI processor automatically."
  echo "    Create it manually at: https://console.cloud.google.com/ai/document-ai"
fi

# ---------------------------------------------------------------------------
# 11. Deploy placeholder Cloud Run services
# ---------------------------------------------------------------------------
echo "==> Deploying Cloud Run backend service..."
gcloud run deploy "${BACKEND_SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="gcr.io/cloudrun/hello" \
  --service-account="${BACKEND_SA_EMAIL}" \
  --vpc-connector="${CONNECTOR_NAME}" \
  --vpc-egress=private-ranges-only \
  --min-instances=1 \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1 \
  --port=8000 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},GCS_DOCUMENTS_BUCKET=${DOCUMENTS_BUCKET}" \
  --quiet || true

FRONTEND_SA_EMAIL="${FRONTEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "==> Deploying Cloud Run frontend service..."
gcloud run deploy "${FRONTEND_SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="gcr.io/cloudrun/hello" \
  --service-account="${FRONTEND_SA_EMAIL}" \
  --min-instances=1 \
  --max-instances=5 \
  --memory=512Mi \
  --cpu=1 \
  --port=3000 \
  --allow-unauthenticated \
  --quiet || true

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "======================================================================"
echo "  GCP setup complete for project: ${PROJECT_ID}"
echo "======================================================================"
echo ""
echo "  Next steps:"
echo "  1. Populate Secret Manager secrets with actual values"
echo "  2. Push your container images to Artifact Registry:"
echo "     ${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/backend:latest"
echo "     ${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/frontend:latest"
echo "  3. Re-deploy Cloud Run services with the production images"
echo "  4. Configure Auth0, Xero, and Microsoft Graph credentials"
echo "  5. Run database migrations: alembic upgrade head"
echo ""
