resource "digitalocean_spaces_bucket" "files" {
  name   = "ndis-crm-files"
  region = var.region
  acl    = "private"
}

resource "digitalocean_spaces_bucket_cors_configuration" "files" {
  bucket = digitalocean_spaces_bucket.files.id
  region = var.region

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET"]
    allowed_origins = ["*"]
    max_age_seconds = 3600
  }
}
