# ---------------------------------------------------------------------------
# Cloud SQL — PostgreSQL 15 (private IP, High Availability)
# ---------------------------------------------------------------------------
resource "google_sql_database_instance" "main" {
  name             = "ndis-crm-postgres"
  database_version = var.db_version
  region           = var.region
  project          = var.project_id

  # Prevent accidental deletion of the production database
  deletion_protection = true

  settings {
    tier              = var.db_tier
    availability_type = "REGIONAL" # High Availability with automatic failover
    disk_type         = "PD_SSD"
    disk_size         = 20
    disk_autoresize   = true

    # Private IP only — no public endpoint exposed
    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.main.id
      enable_private_path_for_google_cloud_services = true
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "02:00" # 2 AM Sydney time (UTC+11 AEDT / UTC+10 AEST)
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30
        retention_unit   = "COUNT"
      }
    }

    maintenance_window {
      day          = 7  # Sunday
      hour         = 3  # 3 AM UTC
      update_track = "stable"
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }
    database_flags {
      name  = "log_disconnections"
      value = "on"
    }
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = false
    }

    user_labels = {
      environment = var.environment
      project     = "ndis-crm"
    }
  }

  depends_on = [
    google_service_networking_connection.private_vpc,
    google_project_service.apis["sqladmin.googleapis.com"],
  ]
}

# Application database
resource "google_sql_database" "main" {
  name     = var.db_name
  instance = google_sql_database_instance.main.name
  project  = var.project_id
}

# Application database user (password stored in Secret Manager)
resource "google_sql_user" "app_user" {
  name     = var.db_user
  instance = google_sql_database_instance.main.name
  project  = var.project_id
  password = random_password.db_password.result
}

resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}
