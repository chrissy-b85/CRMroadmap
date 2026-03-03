resource "google_document_ai_processor" "invoice_parser" {
  project      = var.project_id
  location     = "us" # Document AI is only available in us or eu
  display_name = "ndis-crm-invoice-parser"
  type         = "INVOICE_PROCESSOR"

  depends_on = [google_project_service.apis]
}
