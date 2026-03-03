import type {
  PlanBudgetSummary,
  Plan,
  InvoiceListResponse,
} from '@/lib/types/portal'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!res.ok) {
    const error = await res.text().catch(() => res.statusText)
    throw new Error(error || `HTTP ${res.status}`)
  }

  return res.json() as Promise<T>
}

export async function getMyBudgetSummary(): Promise<PlanBudgetSummary> {
  return apiFetch<PlanBudgetSummary>('/api/v1/portal/budget/summary')
}

export async function getMyBudgetHistory(): Promise<Plan[]> {
  return apiFetch<Plan[]>('/api/v1/portal/budget/history')
}

export async function getMyInvoices(status?: string): Promise<InvoiceListResponse> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : ''
  return apiFetch<InvoiceListResponse>(`/api/v1/portal/invoices${qs}`)
}
