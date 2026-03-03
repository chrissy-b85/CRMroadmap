import type {
  BudgetAlert,
  BurnRate,
  ParticipantBudgetOverview,
  PlanBudgetSummary,
} from '@/lib/types/budget'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const error = await res.text().catch(() => res.statusText)
    throw new Error(error || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function getPlanBudgetSummary(planId: string): Promise<PlanBudgetSummary> {
  return apiFetch<PlanBudgetSummary>(`/api/v1/budget/plans/${planId}/summary`)
}

export async function getPlanBurnRates(planId: string): Promise<BurnRate[]> {
  return apiFetch<BurnRate[]>(`/api/v1/budget/plans/${planId}/burn-rate`)
}

export async function getParticipantBudgetOverview(
  participantId: string
): Promise<ParticipantBudgetOverview> {
  return apiFetch<ParticipantBudgetOverview>(
    `/api/v1/budget/participants/${participantId}/overview`
  )
}

export async function getAllBudgetAlerts(severity?: string): Promise<BudgetAlert[]> {
  const qs = severity ? `?severity=${severity}` : ''
  return apiFetch<BudgetAlert[]>(`/api/v1/budget/alerts${qs}`)
}

export async function recalculateBudget(planId: string): Promise<void> {
  await apiFetch(`/api/v1/budget/plans/${planId}/recalculate`, { method: 'POST' })
}
