'use client'

import { useCallback, useEffect, useState } from 'react'
import type { Invoice, InvoiceStatus } from '@/lib/types/invoice'
import {
  getMyInvoices,
  participantApproveInvoice,
  participantQueryInvoice,
} from '@/lib/api/portal'
import InvoiceApprovalCard from '@/components/portal/InvoiceApprovalCard'
import InvoiceDetailSheet from '@/components/portal/InvoiceDetailSheet'
import PushNotificationSetup from '@/components/portal/PushNotificationSetup'

type TabValue = InvoiceStatus | 'all'

const STATUS_TABS: { label: string; value: TabValue; filter?: string }[] = [
  { label: 'All', value: 'all' },
  {
    label: 'Awaiting My Approval',
    value: 'pending_approval',
    filter: 'PENDING_APPROVAL',
  },
  { label: 'Approved', value: 'approved', filter: 'APPROVED' },
  { label: 'Queried', value: 'info_requested', filter: 'INFO_REQUESTED' },
]

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between">
        <div className="space-y-2">
          <div className="h-4 w-32 rounded bg-gray-200" />
          <div className="h-3 w-24 rounded bg-gray-100" />
        </div>
        <div className="h-5 w-20 rounded-full bg-gray-200" />
      </div>
      <div className="mb-1 h-8 w-28 rounded bg-gray-200" />
      <div className="h-3 w-40 rounded bg-gray-100" />
    </div>
  )
}

export default function PortalInvoicesPage() {
  const [activeTab, setActiveTab] = useState<TabValue>('all')
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null)

  const currentTab = STATUS_TABS.find((t) => t.value === activeTab)

  const fetchInvoices = useCallback(
    async (silent = false) => {
      if (!silent) setLoading(true)
      setError(null)
      try {
        const res = await getMyInvoices(currentTab?.filter)
        setInvoices(res.items)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load invoices')
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [currentTab?.filter]
  )

  useEffect(() => {
    void fetchInvoices()
  }, [fetchInvoices])

  // Pull-to-refresh (touch devices)
  useEffect(() => {
    if (refreshing) void fetchInvoices(true)
  }, [refreshing, fetchInvoices])

  function handleInvoiceUpdated(updated: Invoice) {
    setInvoices((prev) =>
      prev.map((inv) => (inv.id === updated.id ? updated : inv))
    )
    if (selectedInvoice?.id === updated.id) {
      setSelectedInvoice(updated)
    }
  }

  async function handleApprove(id: string) {
    const updated = await participantApproveInvoice(id)
    handleInvoiceUpdated(updated)
  }

  async function handleQuery(id: string, message: string) {
    const updated = await participantQueryInvoice(id, message)
    handleInvoiceUpdated(updated)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="sticky top-0 z-10 border-b border-gray-200 bg-white px-4 pt-safe">
        <h1 className="py-4 text-xl font-bold text-gray-900">My Invoices</h1>

        {/* Status filter tabs */}
        <nav className="-mb-px flex gap-4 overflow-x-auto">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.value}
              type="button"
              onClick={() => setActiveTab(tab.value)}
              className={`whitespace-nowrap border-b-2 pb-3 text-sm font-medium transition-colors ${
                activeTab === tab.value
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="pb-safe">
        {/* Push notification prompt */}
        <div className="pt-4">
          <PushNotificationSetup />
        </div>

        {/* Error state */}
        {error && (
          <div className="mx-4 mt-2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Invoice cards */}
        <div className="space-y-3 px-4 py-3">
          {loading
            ? Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)
            : invoices.map((invoice) => (
                <div key={invoice.id} className="relative">
                  <InvoiceApprovalCard
                    invoice={invoice}
                    onApprove={handleApprove}
                    onQuery={handleQuery}
                  />
                  {/* Review button to open detail sheet */}
                  <button
                    type="button"
                    onClick={() => setSelectedInvoice(invoice)}
                    className="absolute right-4 top-4 rounded-lg bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600 hover:bg-gray-200"
                  >
                    Review
                  </button>
                </div>
              ))}

          {/* Empty state */}
          {!loading && invoices.length === 0 && !error && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <span className="mb-3 text-5xl">🎉</span>
              <p className="text-base font-semibold text-gray-700">
                No invoices to review
              </p>
              <p className="mt-1 text-sm text-gray-400">
                You&apos;re all caught up!
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Invoice detail bottom sheet */}
      {selectedInvoice && (
        <InvoiceDetailSheet
          invoice={selectedInvoice}
          onClose={() => setSelectedInvoice(null)}
          onUpdated={handleInvoiceUpdated}
        />
      )}
    </div>
  )
}
