export interface SupportCategoryBudgetStatus {
  category_id: string
  ndis_support_category: string
  budget_allocated: string
  budget_spent: string
  budget_remaining: string
  utilisation_percent: number
  is_overspent: boolean
  burn_rate_weekly: string | null
  projected_exhaustion_date: string | null
  alert_level: 'warning' | 'critical' | 'overspent' | null
}

export interface BudgetAlert {
  alert_type: 'WARNING' | 'CRITICAL' | 'OVERSPENT' | 'PLAN_EXPIRING' | 'UNDERSPENT'
  category_id: string | null
  category_name: string | null
  message: string
  severity: 'info' | 'warning' | 'critical'
}

export interface PlanBudgetSummary {
  plan_id: string
  participant_id: string
  plan_start_date: string
  plan_end_date: string
  days_remaining: number
  total_allocated: string
  total_spent: string
  total_remaining: string
  overall_utilisation_percent: number
  categories: SupportCategoryBudgetStatus[]
  alerts: BudgetAlert[]
}

export interface BurnRate {
  category_id: string
  avg_weekly_spend: string
  avg_monthly_spend: string
  weeks_remaining_at_current_rate: number | null
  projected_exhaustion_date: string | null
}

export interface ParticipantBudgetOverview {
  participant_id: string
  current_plan: PlanBudgetSummary | null
  historical_plans: Record<string, string>[]
}
