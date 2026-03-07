variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "DigitalOcean region slug"
  type        = string
  default     = "syd1"
}

variable "app_name" {
  description = "Base name used for resources"
  type        = string
  default     = "ndis-crm"
}

variable "db_size" {
  description = "Managed database node size slug for PostgreSQL"
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "redis_size" {
  description = "Managed database node size slug for Redis"
  type        = string
  default     = "db-s-1vcpu-1gb"
}
