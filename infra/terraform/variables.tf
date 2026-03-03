variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "ndis-crm-prod"
}

variable "region" {
  description = "GCP region — australia-southeast1 (Sydney) for data sovereignty"
  type        = string
  default     = "australia-southeast1"
}

variable "environment" {
  description = "Deployment environment label"
  type        = string
  default     = "prod"
}

# ---------------------------------------------------------------------------
# Cloud SQL
# ---------------------------------------------------------------------------
variable "db_tier" {
  description = "Cloud SQL machine tier (e.g. db-g1-small, db-n1-standard-1)"
  type        = string
  default     = "db-g1-small"
}

variable "db_version" {
  description = "PostgreSQL version for Cloud SQL"
  type        = string
  default     = "POSTGRES_15"
}

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "ndis_crm"
}

variable "db_user" {
  description = "Name of the PostgreSQL application user"
  type        = string
  default     = "ndis_crm_app"
}

# ---------------------------------------------------------------------------
# Cloud Run
# ---------------------------------------------------------------------------
variable "backend_image" {
  description = "Container image URI for the FastAPI backend service"
  type        = string
  default     = "australia-southeast1-docker.pkg.dev/ndis-crm-prod/ndis-crm/backend:latest"
}

variable "frontend_image" {
  description = "Container image URI for the Next.js frontend service"
  type        = string
  default     = "australia-southeast1-docker.pkg.dev/ndis-crm-prod/ndis-crm/frontend:latest"
}

# ---------------------------------------------------------------------------
# VPC Serverless Connector
# ---------------------------------------------------------------------------
variable "vpc_connector_cidr" {
  description = "/28 CIDR for the VPC Serverless Connector subnet"
  type        = string
  default     = "10.8.0.0/28"
}
