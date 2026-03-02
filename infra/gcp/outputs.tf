output "backend_cloud_run_url" {
  description = "URL of the backend Cloud Run service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_cloud_run_url" {
  description = "URL of the frontend Cloud Run service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "db_connection_name" {
  description = "Cloud SQL instance connection name for use with Cloud SQL Auth Proxy"
  value       = google_sql_database_instance.ndis_crm_db.connection_name
}

output "db_private_ip" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.ndis_crm_db.private_ip_address
}

output "invoices_bucket_name" {
  description = "Name of the GCS bucket for invoice PDF uploads"
  value       = google_storage_bucket.invoices.name
}

output "documents_bucket_name" {
  description = "Name of the GCS bucket for participant documents"
  value       = google_storage_bucket.documents.name
}

output "statements_bucket_name" {
  description = "Name of the GCS bucket for PDF statements"
  value       = google_storage_bucket.statements.name
}

output "document_ai_processor_id" {
  description = "Document AI processor ID for invoice parsing"
  value       = google_document_ai_processor.invoice_parser.id
}

output "backend_service_account_email" {
  description = "Email of the backend service account"
  value       = google_service_account.backend.email
}

output "frontend_service_account_email" {
  description = "Email of the frontend service account"
  value       = google_service_account.frontend.email
}
