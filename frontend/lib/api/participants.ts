import type {
  AuditLogEntry,
  Participant,
  ParticipantListResponse,
  ParticipantStatus,
  Plan,
} from '@/lib/types/participant'

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

export async function getParticipants(params: {
  page?: number
  pageSize?: number
  search?: string
  status?: ParticipantStatus
}): Promise<ParticipantListResponse> {
  const query = new URLSearchParams()
  if (params.page != null) query.set('page', String(params.page))
  if (params.pageSize != null) query.set('page_size', String(params.pageSize))
  if (params.search) query.set('search', params.search)
  if (params.status) query.set('status', params.status)
  const qs = query.toString()
  return apiFetch<ParticipantListResponse>(`/api/v1/participants${qs ? `?${qs}` : ''}`)
}

export async function getParticipant(id: string): Promise<Participant> {
  return apiFetch<Participant>(`/api/v1/participants/${id}`)
}

export async function getParticipantPlans(id: string): Promise<Plan[]> {
  return apiFetch<Plan[]>(`/api/v1/participants/${id}/plans`)
}

export async function getParticipantAuditLog(id: string): Promise<AuditLogEntry[]> {
  return apiFetch<AuditLogEntry[]>(`/api/v1/participants/${id}/audit-log`)
}

export async function createParticipant(data: Partial<Participant>): Promise<Participant> {
  return apiFetch<Participant>('/api/v1/participants', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateParticipant(
  id: string,
  data: Partial<Participant>
): Promise<Participant> {
  return apiFetch<Participant>(`/api/v1/participants/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}
