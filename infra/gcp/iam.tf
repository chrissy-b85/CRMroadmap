# Backend service account
resource "google_service_account" "backend" {
  project      = var.project_id
  account_id   = "ndis-crm-backend"
  display_name = "NDIS CRM Backend Service Account"

  depends_on = [google_project_service.apis]
}

# Frontend service account
resource "google_service_account" "frontend" {
  project      = var.project_id
  account_id   = "ndis-crm-frontend"
  display_name = "NDIS CRM Frontend Service Account"

  depends_on = [google_project_service.apis]
}

# Backend IAM roles
resource "google_project_iam_member" "backend_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_documentai_user" {
  project = var.project_id
  role    = "roles/documentai.apiUser"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# Frontend IAM roles (minimal — Cloud Run invoker only)
resource "google_project_iam_member" "frontend_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.frontend.email}"
}
