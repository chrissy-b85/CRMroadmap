/**
 * Portal API client — participant-facing endpoints.
 */
import type { Invoice, InvoiceListResponse } from '@/lib/types/invoice'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function portalFetch<T>(
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

  if (res.status === 204) return undefined as unknown as T
  return res.json() as Promise<T>
}

export async function getMyInvoices(
  status?: string
): Promise<InvoiceListResponse> {
  const query = new URLSearchParams()
  if (status) query.set('invoice_status', status)
  const qs = query.toString()
  return portalFetch<InvoiceListResponse>(
    `/api/v1/invoices/my-invoices${qs ? `?${qs}` : ''}`
  )
}

export async function participantApproveInvoice(id: string): Promise<Invoice> {
  return portalFetch<Invoice>(`/api/v1/invoices/${id}/participant-approve`, {
    method: 'POST',
  })
}

export async function participantQueryInvoice(
  id: string,
  message: string
): Promise<Invoice> {
  const query = new URLSearchParams({ message })
  return portalFetch<Invoice>(
    `/api/v1/invoices/${id}/participant-query?${query.toString()}`,
    { method: 'POST' }
  )
}

export async function subscribeToPushNotifications(
  subscription: PushSubscription
): Promise<void> {
  const sub = subscription.toJSON()
  return portalFetch<void>('/api/v1/invoices/push/subscribe', {
    method: 'POST',
    body: JSON.stringify(sub),
  })
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
