output "backend_url" {
  description = "Cloud Run URL for the FastAPI backend"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "Cloud Run URL for the Next.js frontend"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL instance connection name (project:region:instance)"
  value       = google_sql_database_instance.main.connection_name
}

output "cloud_sql_private_ip" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.private_ip_address
}

output "documents_bucket_name" {
  description = "Name of the GCS bucket for document storage"
  value       = google_storage_bucket.documents.name
}

output "backups_bucket_name" {
  description = "Name of the GCS bucket for database backups"
  value       = google_storage_bucket.backups.name
}

output "backend_service_account_email" {
  description = "Email of the backend Cloud Run service account"
  value       = google_service_account.backend.email
}

output "deploy_service_account_email" {
  description = "Email of the CI/CD deploy service account"
  value       = google_service_account.deploy.email
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository name for container images"
  value       = google_artifact_registry_repository.ndis_crm.name
}

output "vpc_network_name" {
  description = "VPC network name"
  value       = google_compute_network.main.name
}

output "vpc_connector_name" {
  description = "VPC Serverless Connector name for Cloud Run → Cloud SQL access"
  value       = google_vpc_access_connector.main.name
}
