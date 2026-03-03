import type {
  Invoice,
  InvoiceListResponse,
  InvoiceStatus,
  ValidationReport,
} from '@/lib/types/invoice'

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

export async function getInvoices(params: {
  page?: number
  pageSize?: number
  status?: InvoiceStatus
  participantId?: string
  providerId?: string
  search?: string
}): Promise<InvoiceListResponse> {
  const query = new URLSearchParams()
  if (params.page != null) query.set('page', String(params.page))
  if (params.pageSize != null) query.set('page_size', String(params.pageSize))
  if (params.status) query.set('status', params.status)
  if (params.participantId) query.set('participant_id', params.participantId)
  if (params.providerId) query.set('provider_id', params.providerId)
  if (params.search) query.set('search', params.search)
  const qs = query.toString()
  return apiFetch<InvoiceListResponse>(`/api/v1/invoices${qs ? `?${qs}` : ''}`)
}

export async function getInvoice(id: string): Promise<Invoice> {
  return apiFetch<Invoice>(`/api/v1/invoices/${id}`)
}

export async function approveInvoice(id: string, notes?: string): Promise<Invoice> {
  return apiFetch<Invoice>(`/api/v1/invoices/${id}/approve`, {
    method: 'POST',
    body: JSON.stringify({ notes: notes ?? null }),
  })
}

export async function rejectInvoice(id: string, reason: string): Promise<Invoice> {
  return apiFetch<Invoice>(`/api/v1/invoices/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

export async function requestInfo(id: string, message: string): Promise<Invoice> {
  return apiFetch<Invoice>(`/api/v1/invoices/${id}/request-info`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

export async function triggerValidation(id: string): Promise<ValidationReport> {
  return apiFetch<ValidationReport>(`/api/v1/invoices/${id}/validate`, {
    method: 'POST',
  })
}
