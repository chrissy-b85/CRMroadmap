export type ParticipantStatus = 'active' | 'inactive' | 'plan_review_pending'

export interface Participant {
  id: string
  ndis_number: string
  legal_name: string
  preferred_name: string | null
  date_of_birth: string
  email: string | null
  phone: string | null
  address: string | null
  status: ParticipantStatus
  portal_access: boolean
  auth0_sub: string | null
  created_at: string
  updated_at: string
}

export interface ParticipantListResponse {
  items: Participant[]
  total: number
  page: number
  page_size: number
}

export interface Plan {
  id: string
  participant_id: string
  plan_start_date: string
  plan_end_date: string
  total_budget: string
  status: 'active' | 'closed' | 'expired'
  support_categories: SupportCategory[]
}

export interface SupportCategory {
  id: string
  ndis_support_category: string
  budget_allocated: string
  budget_spent: string
  budget_remaining: string
  utilisation_percent: number
  alert_level: 'warning' | 'critical' | 'overspent' | null
}

export interface AuditLogEntry {
  id: string
  action: string
  performed_by: string
  timestamp: string
  changes: Record<string, { before: unknown; after: unknown }> | null
}
