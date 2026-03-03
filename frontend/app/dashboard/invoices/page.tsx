'use client'

import { useCallback, useEffect, useState } from 'react'
import { Search, AlertTriangle } from 'lucide-react'
import type { Invoice, InvoiceStatus } from '@/lib/types/invoice'
import { getInvoices } from '@/lib/api/invoices'
import InvoiceStatusBadge from '@/components/invoices/InvoiceStatusBadge'
import OCRConfidenceBar from '@/components/invoices/OCRConfidenceBar'
import InvoiceDetailModal from '@/components/invoices/InvoiceDetailModal'

type SortField = 'invoice_date' | 'total_amount' | 'status' | 'ocr_confidence'
type SortDir = 'asc' | 'desc'

const STATUS_TABS: { label: string; value: InvoiceStatus | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Queued', value: 'queued' },
  { label: 'Flagged', value: 'flagged' },
  { label: 'Pending Approval', value: 'pending_approval' },
  { label: 'Approved', value: 'approved' },
  { label: 'Rejected', value: 'rejected' },
]

const PAGE_SIZE = 20

function SkeletonRow() {
  return (
    <tr className="animate-pulse">
      {Array.from({ length: 8 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 rounded bg-gray-200" />
        </td>
      ))}
    </tr>
  )
}

export default function InvoicesPage() {
  const [activeTab, setActiveTab] = useState<InvoiceStatus | 'all'>('all')
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [sortField, setSortField] = useState<SortField>('invoice_date')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [page, setPage] = useState(1)

  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null)

  // Debounce search input
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 400)
    return () => clearTimeout(t)
  }, [search])

  const fetchInvoices = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getInvoices({
        page,
        pageSize: PAGE_SIZE,
        status: activeTab === 'all' ? undefined : activeTab,
        search: debouncedSearch || undefined,
      })
      setInvoices(res.items)
      setTotal(res.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load invoices')
    } finally {
      setLoading(false)
    }
  }, [page, activeTab, debouncedSearch])

  useEffect(() => {
    void fetchInvoices()
  }, [fetchInvoices])

  // Reset page when filters change
  useEffect(() => {
    setPage(1)
  }, [activeTab, debouncedSearch])

  function toggleSort(field: SortField) {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortDir('asc')
    }
  }

  // Client-side sort (server doesn't support sort params in this spec)
  const sorted = [...invoices].sort((a, b) => {
    let cmp = 0
    if (sortField === 'invoice_date') {
      cmp = (a.invoice_date ?? '').localeCompare(b.invoice_date ?? '')
    } else if (sortField === 'total_amount') {
      cmp = parseFloat(a.total_amount) - parseFloat(b.total_amount)
    } else if (sortField === 'status') {
      cmp = a.status.localeCompare(b.status)
    } else if (sortField === 'ocr_confidence') {
      cmp = (a.ocr_confidence ?? 0) - (b.ocr_confidence ?? 0)
    }
    return sortDir === 'asc' ? cmp : -cmp
  })

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  function SortIcon({ field }: { field: SortField }) {
    if (sortField !== field) return <span className="ml-1 text-gray-300">↕</span>
    return <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>
  }

  function handleInvoiceUpdated(updated: Invoice) {
    setInvoices((prev) =>
      prev.map((inv) => (inv.id === updated.id ? updated : inv))
    )
    if (selectedInvoice?.id === updated.id) {
      setSelectedInvoice(updated)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Invoice Review Queue</h1>
          <p className="mt-1 text-sm text-gray-500">
            Review, approve, or reject submitted invoices.
          </p>
        </div>

        {/* Status tabs */}
        <div className="mb-4 border-b border-gray-200">
          <nav className="-mb-px flex space-x-6 overflow-x-auto">
            {STATUS_TABS.map((tab) => (
              <button
                key={tab.value}
                type="button"
                onClick={() => setActiveTab(tab.value)}
                className={`whitespace-nowrap border-b-2 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab.value
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Search bar */}
        <div className="mb-4 flex items-center gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by invoice #, provider, or participant…"
              className="w-full rounded-md border border-gray-300 py-2 pl-9 pr-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <span className="text-sm text-gray-500">
            {total} invoice{total !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Error state */}
        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Table */}
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">
                    Invoice #
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">
                    Provider
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">
                    Participant
                  </th>
                  <th
                    className="cursor-pointer px-4 py-3 text-left font-medium text-gray-500 hover:text-gray-800"
                    onClick={() => toggleSort('invoice_date')}
                  >
                    Date
                    <SortIcon field="invoice_date" />
                  </th>
                  <th
                    className="cursor-pointer px-4 py-3 text-right font-medium text-gray-500 hover:text-gray-800"
                    onClick={() => toggleSort('total_amount')}
                  >
                    Amount
                    <SortIcon field="total_amount" />
                  </th>
                  <th
                    className="cursor-pointer px-4 py-3 text-left font-medium text-gray-500 hover:text-gray-800"
                    onClick={() => toggleSort('status')}
                  >
                    Status
                    <SortIcon field="status" />
                  </th>
                  <th
                    className="cursor-pointer px-4 py-3 text-left font-medium text-gray-500 hover:text-gray-800"
                    onClick={() => toggleSort('ocr_confidence')}
                  >
                    OCR Confidence
                    <SortIcon field="ocr_confidence" />
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {loading
                  ? Array.from({ length: 5 }).map((_, i) => (
                      <SkeletonRow key={i} />
                    ))
                  : sorted.map((invoice) => (
                      <tr
                        key={invoice.id}
                        className={
                          invoice.status === 'flagged'
                            ? 'bg-red-50 hover:bg-red-100'
                            : 'hover:bg-gray-50'
                        }
                      >
                        <td className="px-4 py-3 font-medium text-gray-900">
                          {invoice.invoice_number ?? invoice.id.slice(0, 8)}
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {invoice.provider_id ?? '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {invoice.participant_id ?? '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {invoice.invoice_date ?? '—'}
                        </td>
                        <td className="px-4 py-3 text-right font-medium text-gray-900">
                          ${invoice.total_amount}
                        </td>
                        <td className="px-4 py-3">
                          <InvoiceStatusBadge status={invoice.status} />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <OCRConfidenceBar confidence={invoice.ocr_confidence} />
                            {invoice.ocr_confidence != null &&
                              invoice.ocr_confidence < 0.85 && (
                                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                              )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <button
                            type="button"
                            onClick={() => setSelectedInvoice(invoice)}
                            className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
                          >
                            Review
                          </button>
                        </td>
                      </tr>
                    ))}

                {!loading && sorted.length === 0 && (
                  <tr>
                    <td
                      colSpan={8}
                      className="px-4 py-12 text-center text-sm text-gray-500"
                    >
                      No invoices found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t px-4 py-3">
              <p className="text-sm text-gray-500">
                Page {page} of {totalPages}
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Invoice detail modal */}
      {selectedInvoice && (
        <InvoiceDetailModal
          invoice={selectedInvoice}
          onClose={() => setSelectedInvoice(null)}
          onUpdated={handleInvoiceUpdated}
        />
      )}
    </div>
  )
}
