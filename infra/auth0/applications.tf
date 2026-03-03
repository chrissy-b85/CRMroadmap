# Staff Web CRM — Regular Web Application
resource "auth0_client" "staff_portal" {
  name            = "NDIS CRM - Staff Portal"
  description     = "Regular Web Application for NDIS CRM staff"
  app_type        = "regular_web"
  oidc_conformant = true

  callbacks = [
    "http://localhost:3000/api/auth/callback",
    "https://crm.ndis-app.com/api/auth/callback",
  ]

  allowed_logout_urls = [
    "http://localhost:3000",
    "https://crm.ndis-app.com",
  ]

  web_origins = [
    "http://localhost:3000",
    "https://crm.ndis-app.com",
  ]

  jwt_configuration {
    alg = "RS256"
  }
}

# Participant PWA — Single Page Application
resource "auth0_client" "participant_pwa" {
  name            = "NDIS CRM - Participant PWA"
  description     = "Single Page Application for NDIS CRM participants"
  app_type        = "spa"
  oidc_conformant = true

  callbacks = [
    "http://localhost:3001/api/auth/callback",
    "https://app.ndis-app.com/api/auth/callback",
  ]

  allowed_logout_urls = [
    "http://localhost:3001",
    "https://app.ndis-app.com",
  ]

  web_origins = [
    "http://localhost:3001",
    "https://app.ndis-app.com",
  ]

  jwt_configuration {
    alg = "RS256"
  }
}
