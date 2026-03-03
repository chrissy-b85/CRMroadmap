export interface DashboardSummary {
  active_participants: number
  active_plans: number
  invoices_this_month: number
  total_spend_this_month: string
  pending_approvals: number
  flagged_invoices: number
  critical_budget_alerts: number
  plans_expiring_30_days: number
  total_budget_under_management: string
}

export interface SpendByCategory {
  ndis_support_category: string
  total_spend: string
}

export interface SpendOverTime {
  period: string
  total_spend: string
}

export interface InvoiceStatusSummary {
  pending: number
  approved: number
  rejected: number
  flagged: number
  info_requested: number
  other: number
}

export interface ProviderAnalytics {
  provider_id: string
  business_name: string
  invoice_count: number
  total_spend: string
  avg_processing_days: number | null
  rejection_rate: number
}

export interface FlaggedInvoiceSummary {
  invoice_id: string
  invoice_number: string | null
  participant_id: string | null
  provider_id: string | null
  total_amount: string
  invoice_date: string
  failing_rules: string[]
}
