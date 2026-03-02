#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# bootstrap.sh — One-time setup of the Terraform remote state bucket.
#
# Run this script ONCE before running `terraform init` for the first time.
# It creates the GCS bucket used to store Terraform state.
#
# Usage:
#   chmod +x infra/scripts/bootstrap.sh
#   ./infra/scripts/bootstrap.sh
# ---------------------------------------------------------------------------
set -euo pipefail

PROJECT_ID="ndis-crm-prod"
REGION="australia-southeast1"
STATE_BUCKET="${PROJECT_ID}-terraform-state"

echo "==> Authenticating with GCP..."
gcloud auth application-default login --quiet

echo "==> Setting active project to ${PROJECT_ID}..."
gcloud config set project "${PROJECT_ID}"

echo "==> Enabling required bootstrap APIs..."
gcloud services enable storage.googleapis.com \
                       cloudresourcemanager.googleapis.com \
                       iam.googleapis.com

echo "==> Creating Terraform remote state bucket: gs://${STATE_BUCKET}"
if gsutil ls -b "gs://${STATE_BUCKET}" &>/dev/null; then
  echo "    Bucket already exists — skipping creation."
else
  gsutil mb -p "${PROJECT_ID}" \
            -l "${REGION}" \
            -b on \
            "gs://${STATE_BUCKET}"

  # Enable versioning so previous state files can be recovered
  gsutil versioning set on "gs://${STATE_BUCKET}"

  # Prevent public access
  gsutil pap set enforced "gs://${STATE_BUCKET}"

  echo "    Bucket created and versioning enabled."
fi

echo ""
echo "==> Bootstrap complete."
echo "    You can now run:"
echo "      cd infra/terraform"
echo "      terraform init"
echo "      terraform plan"
echo "      terraform apply"
