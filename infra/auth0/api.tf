# NDIS CRM API resource server
resource "auth0_resource_server" "ndis_crm_api" {
  name                                            = "NDIS CRM API"
  identifier                                      = "https://api.ndis-crm.com"
  signing_alg                                     = "RS256"
  enforce_policies                                = true
  token_dialect                                   = "access_token_authz"
  allow_offline_access                            = false
  skip_consent_for_verifiable_first_party_clients = true

  scopes {
    value       = "read:participants"
    description = "Read participant records"
  }

  scopes {
    value       = "write:participants"
    description = "Create and update participant records"
  }

  scopes {
    value       = "read:invoices"
    description = "Read invoice records"
  }

  scopes {
    value       = "write:invoices"
    description = "Create and update invoice records"
  }

  scopes {
    value       = "approve:invoices"
    description = "Approve invoices for payment"
  }

  scopes {
    value       = "read:reports"
    description = "Access reporting and analytics"
  }

  scopes {
    value       = "manage:users"
    description = "Manage user accounts (Admin only)"
  }
}
