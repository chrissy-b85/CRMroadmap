# Enable all GCP APIs required by the NDIS CRM project.
# Terraform manages the enable/disable lifecycle — removing an entry here
# will disable the API on next apply (use with caution in production).

locals {
  required_apis = [
    "run.googleapis.com",              # Cloud Run
    "sql-component.googleapis.com",    # Cloud SQL component
    "sqladmin.googleapis.com",         # Cloud SQL Admin API
    "storage.googleapis.com",          # Google Cloud Storage
    "documentai.googleapis.com",       # Document AI (invoice OCR)
    "secretmanager.googleapis.com",    # Secret Manager
    "vpcaccess.googleapis.com",        # VPC Serverless Connector
    "servicenetworking.googleapis.com",# Private service networking (Cloud SQL private IP)
    "compute.googleapis.com",          # Compute Engine (VPC, networking)
    "iam.googleapis.com",              # IAM
    "cloudresourcemanager.googleapis.com", # Resource Manager
    "artifactregistry.googleapis.com", # Artifact Registry (container images)
    "cloudbuild.googleapis.com",       # Cloud Build (CI/CD)
    "redis.googleapis.com",            # Memorystore for Redis (task queue)
    "monitoring.googleapis.com",       # Cloud Monitoring
    "logging.googleapis.com",          # Cloud Logging
  ]
}

resource "google_project_service" "apis" {
  for_each = toset(local.required_apis)

  project = var.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}
