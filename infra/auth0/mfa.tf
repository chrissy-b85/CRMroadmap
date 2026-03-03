# Enable MFA Guardian factors
resource "auth0_guardian" "mfa" {
  policy = "always"

  otp = true
}

# Enforce MFA for the Staff Portal application
resource "auth0_client_grant" "staff_portal_mfa" {
  client_id = auth0_client.staff_portal.id
  audience  = "https://${var.auth0_domain}/mfa/"
  scopes    = ["enroll", "read:authenticators", "remove:authenticators"]
}
