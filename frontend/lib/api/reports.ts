import type {
  DashboardSummary,
  FlaggedInvoiceSummary,
  InvoiceStatusSummary,
  ProviderAnalytics,
  SpendByCategory,
  SpendOverTime,
} from '@/lib/types/reports'

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

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>('/api/v1/reports/dashboard-summary')
}

export async function getSpendByCategory(params: {
  dateFrom: string
  dateTo: string
  participantId?: string
}): Promise<SpendByCategory[]> {
  const q = new URLSearchParams({ date_from: params.dateFrom, date_to: params.dateTo })
  if (params.participantId) q.set('participant_id', params.participantId)
  return apiFetch<SpendByCategory[]>(`/api/v1/reports/spend-by-category?${q}`)
}

export async function getSpendOverTime(params: {
  granularity?: 'week' | 'month'
  dateFrom?: string
  dateTo?: string
}): Promise<SpendOverTime[]> {
  const q = new URLSearchParams()
  if (params.granularity) q.set('granularity', params.granularity)
  if (params.dateFrom) q.set('date_from', params.dateFrom)
  if (params.dateTo) q.set('date_to', params.dateTo)
  return apiFetch<SpendOverTime[]>(`/api/v1/reports/spend-over-time?${q}`)
}

export async function getInvoiceStatusSummary(): Promise<InvoiceStatusSummary> {
  return apiFetch<InvoiceStatusSummary>('/api/v1/reports/invoice-status-summary')
}

export async function getProviderAnalytics(params: {
  dateFrom: string
  dateTo: string
}): Promise<ProviderAnalytics[]> {
  const q = new URLSearchParams({ date_from: params.dateFrom, date_to: params.dateTo })
  return apiFetch<ProviderAnalytics[]>(`/api/v1/reports/provider-analytics?${q}`)
}

export async function getFlaggedInvoicesSummary(): Promise<FlaggedInvoiceSummary[]> {
  return apiFetch<FlaggedInvoiceSummary[]>('/api/v1/reports/flagged-invoices-summary')
}
