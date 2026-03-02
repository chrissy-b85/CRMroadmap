# ---------------------------------------------------------------------------
# Secret Manager secrets
#
# Secret *resources* (the containers) are created here with Terraform.
# Secret *values* must be populated separately (never committed to version
# control).  After applying this config, populate each secret with:
#   echo -n "VALUE" | gcloud secrets versions add SECRET_ID --data-file=-
# ---------------------------------------------------------------------------

# PostgreSQL asyncpg connection string
resource "google_secret_manager_secret" "database_url" {
  secret_id = "database-url"
  project   = var.project_id

  replication {
    user_managed {
      replicas { location = var.region }
    }
  }

  labels = { environment = var.environment, project = "ndis-crm" }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

# Redis connection string
resource "google_secret_manager_secret" "redis_url" {
  secret_id = "redis-url"
  project   = var.project_id

  replication {
    user_managed {
      replicas { location = var.region }
    }
  }

  labels = { environment = var.environment, project = "ndis-crm" }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

# Auth0 tenant domain (e.g. your-tenant.au.auth0.com)
resource "google_secret_manager_secret" "auth0_domain" {
  secret_id = "auth0-domain"
  project   = var.project_id

  replication {
    user_managed {
      replicas { location = var.region }
    }
  }

  labels = { environment = var.environment, project = "ndis-crm" }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

# Auth0 API audience identifier
resource "google_secret_manager_secret" "auth0_audience" {
  secret_id = "auth0-audience"
  project   = var.project_id

  replication {
    user_managed {
      replicas { location = var.region }
    }
  }

  labels = { environment = var.environment, project = "ndis-crm" }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

# Auth0 SPA client ID (frontend)
resource "google_secret_manager_secret" "auth0_client_id" {
  secret_id = "auth0-client-id"
  project   = var.project_id

  replication {
    user_managed {
      replicas { location = var.region }
    }
  }

  labels = { environment = var.environment, project = "ndis-crm" }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

# Auth0 backend client secret
resource "google_secret_manager_secret" "auth0_client_secret" {
  secret_id = "auth0-client-secret"
  project   = var.project_id

  replication {
    user_managed {
      replicas { location = var.region }
    }
  }

  labels = { environment = var.environment, project = "ndis-crm" }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

# Xero OAuth 2.0 client ID
resource "google_secret_manager_secret" "xero_client_id" {
  secret_id = "xero-client-id"
  project   = var.project_id

  replication {
    user_managed {
      replicas { location = var.region }
    }
  }

  labels = { environment = var.environment, project = "ndis-crm" }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

# Xero OAuth 2.0 client secret
resource "google_secret_manager_secret" "xero_client_secret" {
  secret_id = "xero-client-secret"
  project   = var.project_id

  replication {
    user_managed {
      replicas { location = var.region }
    }
  }

  labels = { environment = var.environment, project = "ndis-crm" }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

# Microsoft Graph API (Outlook) client ID
resource "google_secret_manager_secret" "msgraph_client_id" {
  secret_id = "msgraph-client-id"
  project   = var.project_id

  replication {
    user_managed {
      replicas { location = var.region }
    }
  }

  labels = { environment = var.environment, project = "ndis-crm" }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

# Microsoft Graph API (Outlook) client secret
resource "google_secret_manager_secret" "msgraph_client_secret" {
  secret_id = "msgraph-client-secret"
  project   = var.project_id

  replication {
    user_managed {
      replicas { location = var.region }
    }
  }

  labels = { environment = var.environment, project = "ndis-crm" }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

# Microsoft Graph API tenant ID
resource "google_secret_manager_secret" "msgraph_tenant_id" {
  secret_id = "msgraph-tenant-id"
  project   = var.project_id

  replication {
    user_managed {
      replicas { location = var.region }
    }
  }

  labels = { environment = var.environment, project = "ndis-crm" }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

# Google Document AI processor ID (created after enabling the API)
resource "google_secret_manager_secret" "document_ai_processor_id" {
  secret_id = "document-ai-processor-id"
  project   = var.project_id

  replication {
    user_managed {
      replicas { location = var.region }
    }
  }

  labels = { environment = var.environment, project = "ndis-crm" }
  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

