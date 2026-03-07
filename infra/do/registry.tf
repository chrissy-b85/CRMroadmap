resource "digitalocean_container_registry" "ndis_crm" {
  name                   = "ndis-crm"
  subscription_tier_slug = "basic"
}
