resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}:?"
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_sql_database_instance" "ndis_crm_db" {
  project          = var.project_id
  name             = "ndis-crm-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = var.db_instance_tier

    ip_configuration {
      ipv4_enabled    = false
      private_network = "projects/${var.project_id}/global/networks/default"
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "03:00"
      transaction_log_retention_days = 7

      backup_retention_settings {
        retained_backups = 7
      }
    }

    insights_config {
      query_insights_enabled = true
    }
  }

  deletion_protection = true

  depends_on = [google_project_service.apis]
}

resource "google_sql_database" "ndis_crm" {
  project  = var.project_id
  name     = "ndis_crm"
  instance = google_sql_database_instance.ndis_crm_db.name
}

resource "google_sql_user" "ndis_crm_user" {
  project  = var.project_id
  name     = "ndis_crm_user"
  instance = google_sql_database_instance.ndis_crm_db.name
  password = random_password.db_password.result
}

