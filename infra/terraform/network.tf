# ---------------------------------------------------------------------------
# VPC Network
# ---------------------------------------------------------------------------
resource "google_compute_network" "main" {
  name                    = "ndis-crm-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id

  depends_on = [google_project_service.apis["compute.googleapis.com"]]
}

resource "google_compute_subnetwork" "main" {
  name          = "ndis-crm-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.main.id
  project       = var.project_id

  private_ip_google_access = true
}

# ---------------------------------------------------------------------------
# Private services access (required for Cloud SQL private IP)
# ---------------------------------------------------------------------------
resource "google_compute_global_address" "private_ip_range" {
  name          = "ndis-crm-private-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
  project       = var.project_id

  depends_on = [google_project_service.apis["compute.googleapis.com"]]
}

resource "google_service_networking_connection" "private_vpc" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]

  depends_on = [google_project_service.apis["servicenetworking.googleapis.com"]]
}

# ---------------------------------------------------------------------------
# VPC Serverless Connector — allows Cloud Run to reach Cloud SQL private IP
# ---------------------------------------------------------------------------
resource "google_vpc_access_connector" "main" {
  name          = "ndis-crm-connector"
  region        = var.region
  project       = var.project_id
  ip_cidr_range = var.vpc_connector_cidr
  network       = google_compute_network.main.id
  min_instances = 2
  max_instances = 3
  machine_type  = "e2-micro"

  depends_on = [google_project_service.apis["vpcaccess.googleapis.com"]]
}
