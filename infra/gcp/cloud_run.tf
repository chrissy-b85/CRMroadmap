resource "google_cloud_run_v2_service" "backend" {
  project  = var.project_id
  name     = "ndis-crm-backend"
  location = var.region

  template {
    service_account = google_service_account.backend.email

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    containers {
      image = var.backend_image

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name = "AUTH0_DOMAIN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.auth0_domain.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "AUTH0_AUDIENCE"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.auth0_audience.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "AUTH0_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.auth0_client_secret.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "XERO_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.xero_client_id.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "XERO_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.xero_client_secret.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "OUTLOOK_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.outlook_client_id.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "OUTLOOK_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.outlook_client_secret.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "DOCUMENT_AI_PROCESSOR_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.document_ai_processor_id.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GCP_REGION"
        value = var.region
      }
    }
  }

  depends_on = [
    google_project_service.apis,
    google_service_account.backend,
  ]
}

resource "google_cloud_run_v2_service" "frontend" {
  project  = var.project_id
  name     = "ndis-crm-frontend"
  location = var.region

  template {
    service_account = google_service_account.frontend.email

    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }

    containers {
      image = var.frontend_image

      ports {
        container_port = 3000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
    }
  }

  depends_on = [
    google_project_service.apis,
    google_service_account.frontend,
    google_cloud_run_v2_service.backend,
  ]
}

# Allow unauthenticated access to the frontend
resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
