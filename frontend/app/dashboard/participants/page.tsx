import Link from 'next/link'
import { Search, User, ChevronRight } from 'lucide-react'
import { getParticipants } from '@/lib/api/participants'
import type { ParticipantStatus } from '@/lib/types/participant'

const STATUS_TABS: { label: string; value: ParticipantStatus | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Active', value: 'active' },
  { label: 'Inactive', value: 'inactive' },
  { label: 'Plan Review Pending', value: 'plan_review_pending' },
]

function StatusBadge({ status }: { status: ParticipantStatus }) {
  const classes: Record<ParticipantStatus, string> = {
    active: 'bg-green-100 text-green-800',
    inactive: 'bg-gray-100 text-gray-800',
    plan_review_pending: 'bg-yellow-100 text-yellow-800',
  }
  const labels: Record<ParticipantStatus, string> = {
    active: 'Active',
    inactive: 'Inactive',
    plan_review_pending: 'Plan Review Pending',
  }
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${classes[status]}`}
    >
      {labels[status]}
    </span>
  )
}

interface PageProps {
  searchParams: Promise<{
    search?: string
    status?: string
    page?: string
  }>
}

const PAGE_SIZE = 20

export default async function ParticipantsPage({ searchParams }: PageProps) {
  const params = await searchParams
  const search = params.search ?? ''
  const statusParam = params.status ?? 'all'
  const page = Number(params.page ?? 1)

  const status =
    statusParam !== 'all' &&
    ['active', 'inactive', 'plan_review_pending'].includes(statusParam)
      ? (statusParam as ParticipantStatus)
      : undefined

  const data = await getParticipants({
    page,
    pageSize: PAGE_SIZE,
    search: search || undefined,
    status,
  }).catch(() => null)

  const participants = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  function buildHref(overrides: Record<string, string | undefined>) {
    const merged: Record<string, string> = {}
    if (search) merged.search = search
    if (statusParam !== 'all') merged.status = statusParam
    if (page > 1) merged.page = String(page)
    Object.entries(overrides).forEach(([k, v]) => {
      if (v === undefined) delete merged[k]
      else merged[k] = v
    })
    const qs = new URLSearchParams(merged).toString()
    return `/dashboard/participants${qs ? `?${qs}` : ''}`
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Participants</h1>
          <Link
            href="/dashboard/participants/new"
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            + New Participant
          </Link>
        </div>

        {/* Search */}
        <form method="GET" action="/dashboard/participants" className="mb-6">
          {statusParam !== 'all' && (
            <input type="hidden" name="status" value={statusParam} />
          )}
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              type="search"
              name="search"
              defaultValue={search}
              placeholder="Search by name or NDIS number…"
              className="w-full rounded-md border border-gray-300 bg-white py-2 pl-9 pr-4 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </form>

        {/* Status tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-6">
            {STATUS_TABS.map((tab) => {
              const isActive = statusParam === tab.value
              return (
                <Link
                  key={tab.value}
                  href={buildHref({ status: tab.value === 'all' ? undefined : tab.value, page: undefined })}
                  className={`whitespace-nowrap border-b-2 py-3 text-sm font-medium ${
                    isActive
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  {tab.label}
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Table */}
        <div className="overflow-hidden rounded-lg bg-white shadow">
          {data === null ? (
            <div className="px-4 py-12 text-center text-sm text-red-600">
              Failed to load participants. Please try again.
            </div>
          ) : participants.length === 0 ? (
            <div className="flex flex-col items-center px-4 py-16 text-center">
              <User className="mb-4 h-12 w-12 text-gray-300" />
              <p className="text-sm font-medium text-gray-500">No participants found</p>
              {search && (
                <p className="mt-1 text-xs text-gray-400">
                  Try adjusting your search term.
                </p>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">
                      Legal Name
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">
                      Preferred Name
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">
                      NDIS Number
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">
                      Date of Birth
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">
                      Contact
                    </th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {participants.map((p) => (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">
                        {p.legal_name}
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {p.preferred_name ?? '—'}
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-700">
                        {p.ndis_number}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={p.status} />
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {new Date(p.date_of_birth).toLocaleDateString('en-AU')}
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {p.phone ?? p.email ?? '—'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          href={`/dashboard/participants/${p.id}`}
                          className="inline-flex items-center text-blue-600 hover:text-blue-800"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-6 flex items-center justify-between text-sm text-gray-600">
            <span>
              Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} of{' '}
              {total} participants
            </span>
            <div className="flex gap-2">
              {page > 1 && (
                <Link
                  href={buildHref({ page: String(page - 1) })}
                  className="rounded-md border border-gray-300 bg-white px-3 py-1.5 hover:bg-gray-50"
                >
                  Previous
                </Link>
              )}
              {page < totalPages && (
                <Link
                  href={buildHref({ page: String(page + 1) })}
                  className="rounded-md border border-gray-300 bg-white px-3 py-1.5 hover:bg-gray-50"
                >
                  Next
                </Link>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
