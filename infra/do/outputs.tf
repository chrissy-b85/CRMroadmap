output "postgres_uri" {
  description = "PostgreSQL connection URI"
  value       = digitalocean_database_cluster.postgres.uri
  sensitive   = true
}

output "redis_uri" {
  description = "Redis connection URI"
  value       = digitalocean_database_cluster.redis.uri
  sensitive   = true
}

output "registry_endpoint" {
  description = "Container registry endpoint"
  value       = digitalocean_container_registry.ndis_crm.endpoint
}

output "spaces_bucket_name" {
  description = "Spaces bucket name for file storage"
  value       = digitalocean_spaces_bucket.files.name
}

output "spaces_endpoint" {
  description = "Spaces endpoint URL"
  value       = "https://${var.region}.digitaloceanspaces.com"
}
