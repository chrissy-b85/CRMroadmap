locals {
  secrets = {
    "auth0-domain"               = "Auth0 tenant domain"
    "auth0-audience"             = "Auth0 API audience identifier"
    "auth0-client-secret"        = "Auth0 client secret"
    "db-password"                = "Cloud SQL database password for ndis_crm_user"
    "xero-client-id"             = "Xero API client ID"
    "xero-client-secret"         = "Xero API client secret"
    "outlook-client-id"          = "Microsoft Graph / Outlook client ID"
    "outlook-client-secret"      = "Microsoft Graph / Outlook client secret"
    "document-ai-processor-id"   = "Document AI processor ID for invoice parsing"
  }
}

resource "google_secret_manager_secret" "auth0_domain" {
  project   = var.project_id
  secret_id = "auth0-domain"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "auth0_audience" {
  project   = var.project_id
  secret_id = "auth0-audience"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "auth0_client_secret" {
  project   = var.project_id
  secret_id = "auth0-client-secret"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "db_password" {
  project   = var.project_id
  secret_id = "db-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "xero_client_id" {
  project   = var.project_id
  secret_id = "xero-client-id"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "xero_client_secret" {
  project   = var.project_id
  secret_id = "xero-client-secret"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "outlook_client_id" {
  project   = var.project_id
  secret_id = "outlook-client-id"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "outlook_client_secret" {
  project   = var.project_id
  secret_id = "outlook-client-secret"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "document_ai_processor_id" {
  project   = var.project_id
  secret_id = "document-ai-processor-id"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# Grant backend service account access to all secrets
resource "google_secret_manager_secret_iam_member" "backend_auth0_domain" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.auth0_domain.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_auth0_audience" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.auth0_audience.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_auth0_client_secret" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.auth0_client_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_db_password" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_xero_client_id" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.xero_client_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_xero_client_secret" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.xero_client_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_outlook_client_id" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.outlook_client_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_outlook_client_secret" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.outlook_client_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_document_ai_processor_id" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.document_ai_processor_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}
