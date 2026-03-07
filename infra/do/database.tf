resource "digitalocean_database_cluster" "postgres" {
  name       = "${var.app_name}-postgres"
  engine     = "pg"
  version    = "15"
  size       = var.db_size
  region     = var.region
  node_count = 1
}

resource "digitalocean_database_cluster" "redis" {
  name       = "${var.app_name}-redis"
  engine     = "redis"
  version    = "7"
  size       = var.redis_size
  region     = var.region
  node_count = 1
}

resource "digitalocean_database_db" "ndis_crm" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "ndis_crm"
}
