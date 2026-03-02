# --- Roles ---

resource "auth0_role" "admin" {
  name        = "Admin"
  description = "Full access to all CRM features"
}

resource "auth0_role" "coordinator" {
  name        = "Coordinator"
  description = "Manage participants, plans, and invoices"
}

resource "auth0_role" "viewer" {
  name        = "Viewer"
  description = "Read-only access to CRM data"
}

# --- Role permissions ---

resource "auth0_role_permissions" "admin_permissions" {
  role_id = auth0_role.admin.id

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "read:participants"
  }

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "write:participants"
  }

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "read:invoices"
  }

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "write:invoices"
  }

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "approve:invoices"
  }

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "read:reports"
  }

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "manage:users"
  }
}

resource "auth0_role_permissions" "coordinator_permissions" {
  role_id = auth0_role.coordinator.id

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "read:participants"
  }

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "write:participants"
  }

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "read:invoices"
  }

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "write:invoices"
  }

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "approve:invoices"
  }

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "read:reports"
  }
}

resource "auth0_role_permissions" "viewer_permissions" {
  role_id = auth0_role.viewer.id

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "read:participants"
  }

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "read:invoices"
  }

  permissions {
    resource_server_identifier = auth0_resource_server.ndis_crm_api.identifier
    name                       = "read:reports"
  }
}
