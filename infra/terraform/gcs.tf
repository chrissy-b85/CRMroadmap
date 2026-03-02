# ---------------------------------------------------------------------------
# GCS Bucket — Document Storage
# Stores NDIS plans, invoices, service agreements, statements, and ID documents.
# No public access. Objects accessed via time-limited signed URLs only.
# ---------------------------------------------------------------------------
resource "google_storage_bucket" "documents" {
  name          = "${var.project_id}-documents"
  location      = var.region
  storage_class = "STANDARD"
  project       = var.project_id

  # Prevent accidental deletion of the production bucket
  force_destroy = false

  # Object versioning — recover deleted or overwritten documents
  versioning {
    enabled = true
  }

  # Block all public access
  public_access_prevention = "enforced"

  uniform_bucket_level_access = true

  # Rule 1: Keep only the 3 most recent non-current (archived) versions.
  # Triggers when an object has more than 3 newer versions.
  lifecycle_rule {
    condition {
      num_newer_versions = 3
      with_state         = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  # Rule 2: Hard expiry — delete any remaining archived version after 90 days.
  # Acts as a safety net for long-lived objects that accumulate slowly.
  lifecycle_rule {
    condition {
      age        = 90
      with_state = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["Content-Type", "Content-Disposition"]
    max_age_seconds = 3600
  }

  labels = {
    environment = var.environment
    project     = "ndis-crm"
    data-class  = "sensitive"
  }

  depends_on = [google_project_service.apis["storage.googleapis.com"]]
}

# ---------------------------------------------------------------------------
# GCS Bucket — Database Backups
# Stores Cloud SQL automated and manual backup exports.
# ---------------------------------------------------------------------------
resource "google_storage_bucket" "backups" {
  name          = "${var.project_id}-backups"
  location      = var.region
  storage_class = "NEARLINE"
  project       = var.project_id

  force_destroy = false

  versioning {
    enabled = false
  }

  public_access_prevention    = "enforced"
  uniform_bucket_level_access = true

  # Automatically delete backup files older than 90 days
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    project     = "ndis-crm"
    data-class  = "backup"
  }

  depends_on = [google_project_service.apis["storage.googleapis.com"]]
}

# Grant the Cloud SQL service account write access to the backups bucket
resource "google_storage_bucket_iam_member" "cloudsql_backup_writer" {
  bucket = google_storage_bucket.backups.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${data.google_sql_service_account.main.email}"
}

data "google_sql_service_account" "main" {
  project = var.project_id
}
