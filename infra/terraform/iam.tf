# ---------------------------------------------------------------------------
# Service Accounts
# ---------------------------------------------------------------------------

# Backend service account — used by the Cloud Run FastAPI service
resource "google_service_account" "backend" {
  account_id   = "ndis-crm-backend"
  display_name = "NDIS CRM Backend (Cloud Run)"
  project      = var.project_id

  depends_on = [google_project_service.apis["iam.googleapis.com"]]
}

# Frontend service account — used by the Cloud Run Next.js service
resource "google_service_account" "frontend" {
  account_id   = "ndis-crm-frontend"
  display_name = "NDIS CRM Frontend (Cloud Run)"
  project      = var.project_id

  depends_on = [google_project_service.apis["iam.googleapis.com"]]
}

# CI/CD deploy service account — used by GitHub Actions
resource "google_service_account" "deploy" {
  account_id   = "ndis-crm-deploy"
  display_name = "NDIS CRM CI/CD Deploy (GitHub Actions)"
  project      = var.project_id

  depends_on = [google_project_service.apis["iam.googleapis.com"]]
}

# ---------------------------------------------------------------------------
# IAM bindings — backend service account (least-privilege)
# ---------------------------------------------------------------------------

# Cloud SQL Client — connect to the database via Cloud SQL Auth Proxy
resource "google_project_iam_member" "backend_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# GCS Object Admin — read/write documents bucket objects
resource "google_storage_bucket_iam_member" "backend_documents_admin" {
  bucket = google_storage_bucket.documents.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backend.email}"
}

# Secret Manager Secret Accessor — read secrets at runtime
resource "google_project_iam_member" "backend_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# Document AI API User — submit documents for OCR processing
resource "google_project_iam_member" "backend_documentai_user" {
  project = var.project_id
  role    = "roles/documentai.apiUser"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# Cloud Run Invoker — allow frontend Cloud Run to call backend Cloud Run internally
resource "google_cloud_run_v2_service_iam_member" "frontend_invokes_backend" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.backend.email}"
}

# ---------------------------------------------------------------------------
# IAM bindings — frontend service account (least-privilege)
# ---------------------------------------------------------------------------

# Secret Manager Secret Accessor — read Auth0 domain/client ID for SSR at runtime
resource "google_project_iam_member" "frontend_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.frontend.email}"
}

# ---------------------------------------------------------------------------
# IAM bindings — deploy service account (CI/CD)
# ---------------------------------------------------------------------------

# Cloud Run Developer — deploy new revisions
resource "google_project_iam_member" "deploy_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.deploy.email}"
}

# Artifact Registry Writer — push container images
resource "google_project_iam_member" "deploy_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.deploy.email}"
}

# Act as the backend service account when deploying Cloud Run services
resource "google_service_account_iam_member" "deploy_acts_as_backend" {
  service_account_id = google_service_account.backend.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deploy.email}"
}

# ---------------------------------------------------------------------------
# Artifact Registry — container image repository
# ---------------------------------------------------------------------------
resource "google_artifact_registry_repository" "ndis_crm" {
  location      = var.region
  repository_id = "ndis-crm"
  description   = "Container images for the NDIS CRM application"
  format        = "DOCKER"
  project       = var.project_id

  depends_on = [google_project_service.apis["artifactregistry.googleapis.com"]]
}
