export type InvoiceStatus =
  | 'queued'
  | 'flagged'
  | 'pending_approval'
  | 'info_requested'
  | 'approved'
  | 'rejected'
  | 'paid'

export interface Invoice {
  id: string
  participant_id: string | null
  provider_id: string | null
  invoice_number: string | null
  invoice_date: string | null
  due_date: string | null
  total_amount: string
  gst_amount: string
  status: InvoiceStatus
  ocr_confidence: number | null
  gcs_pdf_path: string
  line_items: InvoiceLineItem[]
  validation_results: ValidationResult[] | null
  reviewed_by: string | null
  reviewed_at: string | null
  created_at: string
  participant_approved: boolean | null
  participant_approved_at: string | null
  participant_query_message: string | null
}

export interface InvoiceLineItem {
  id: string
  support_item_number: string | null
  description: string | null
  unit_price: string
  quantity: string
  total: string
}

export interface ValidationResult {
  rule_name: string
  passed: boolean
  message: string
  severity: 'error' | 'warning'
}

export interface InvoiceListResponse {
  items: Invoice[]
  total: number
  page: number
  page_size: number
}

export interface ValidationReport {
  invoice_id: string
  validated_at: string
  results: ValidationResult[]
  overall_passed: boolean
}
