output "staff_portal_client_id" {
  description = "Client ID for the NDIS CRM Staff Portal application"
  value       = auth0_client.staff_portal.client_id
}

output "participant_pwa_client_id" {
  description = "Client ID for the NDIS CRM Participant PWA application"
  value       = auth0_client.participant_pwa.client_id
}

output "api_audience" {
  description = "Audience (identifier) for the NDIS CRM API resource server"
  value       = auth0_resource_server.ndis_crm_api.identifier
}
