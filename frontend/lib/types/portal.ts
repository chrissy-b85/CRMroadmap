export type BudgetAlertLevel = 'warning' | 'critical' | 'overspent' | null

export interface SupportCategory {
  id: string
  name: string
  icon: string
  allocated: number
  spent: number
  alertLevel: BudgetAlertLevel
  projectedExhaustionDate?: string | null
}

export interface PlanBudgetSummary {
  planId: string
  participantFirstName: string
  participantId: string
  planStartDate: string
  planEndDate: string
  totalAllocated: number
  totalSpent: number
  pendingInvoicesCount: number
  categories: SupportCategory[]
  alerts: BudgetAlert[]
}

export interface BudgetAlert {
  id: string
  level: 'warning' | 'critical'
  categoryId?: string
  message: string
}

export interface Plan {
  planId: string
  planStartDate: string
  planEndDate: string
  totalAllocated: number
  totalSpent: number
  finalUtilisationPercent: number
}

export interface InvoiceListResponse {
  items: PortalInvoice[]
  total: number
  page: number
  page_size: number
}

export interface PortalInvoice {
  id: string
  invoiceNumber: string | null
  invoiceDate: string | null
  totalAmount: number
  status: string
  providerName: string | null
}
