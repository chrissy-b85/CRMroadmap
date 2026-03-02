variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "ndis-crm-prod"
}

variable "region" {
  description = "The GCP region for all resources"
  type        = string
  default     = "australia-southeast1"
}

variable "environment" {
  description = "Deployment environment (e.g. prod, staging)"
  type        = string
  default     = "prod"
}

variable "backend_image" {
  description = "Container image for the backend Cloud Run service"
  type        = string
  default     = "australia-southeast1-docker.pkg.dev/ndis-crm-prod/ndis-crm/backend:latest"
}

variable "frontend_image" {
  description = "Container image for the frontend Cloud Run service"
  type        = string
  default     = "australia-southeast1-docker.pkg.dev/ndis-crm-prod/ndis-crm/frontend:latest"
}

variable "db_instance_tier" {
  description = "Cloud SQL machine type"
  type        = string
  default     = "db-g1-small"
}
