'use client'

import { useState } from 'react'
import type { Invoice } from '@/lib/types/invoice'
import { participantApproveInvoice } from '@/lib/api/portal'
import InvoiceQueryDialog from './InvoiceQueryDialog'

interface InvoiceApprovalCardProps {
  invoice: Invoice
  onApprove: (id: string) => Promise<void>
  onQuery: (id: string, message: string) => Promise<void>
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    PENDING_APPROVAL: 'bg-yellow-100 text-yellow-800',
    pending_approval: 'bg-yellow-100 text-yellow-800',
    APPROVED: 'bg-green-100 text-green-800',
    approved: 'bg-green-100 text-green-800',
    INFO_REQUESTED: 'bg-blue-100 text-blue-800',
    info_requested: 'bg-blue-100 text-blue-800',
    REJECTED: 'bg-red-100 text-red-800',
    rejected: 'bg-red-100 text-red-800',
  }
  const cls = map[status] ?? 'bg-gray-100 text-gray-700'
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}

export default function InvoiceApprovalCard({
  invoice,
  onApprove,
  onQuery,
}: InvoiceApprovalCardProps) {
  const [confirming, setConfirming] = useState(false)
  const [queryOpen, setQueryOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleApprove() {
    if (!confirming) {
      setConfirming(true)
      return
    }
    setLoading(true)
    try {
      await onApprove(invoice.id)
    } finally {
      setLoading(false)
      setConfirming(false)
    }
  }

  const awaitingApproval =
    invoice.status === 'PENDING_APPROVAL' || invoice.status === 'pending_approval'

  return (
    <>
      <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
        {/* Header row */}
        <div className="mb-3 flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-gray-900">
              {invoice.invoice_number ?? `INV-${invoice.id.slice(0, 8)}`}
            </p>
            <p className="mt-0.5 truncate text-xs text-gray-500">
              Provider: {invoice.provider_id ?? '—'}
            </p>
          </div>
          <StatusBadge status={invoice.status} />
        </div>

        {/* Amount */}
        <p className="mb-1 text-3xl font-bold text-gray-900">
          ${parseFloat(invoice.total_amount).toFixed(2)}
        </p>
        <p className="mb-3 text-xs text-gray-500">
          Date: {invoice.invoice_date ?? '—'} &nbsp;·&nbsp; GST: $
          {parseFloat(invoice.gst_amount).toFixed(2)}
        </p>

        {/* Participant-approved indicator */}
        {invoice.participant_approved && (
          <p className="mb-3 text-xs font-medium text-green-700">
            ✓ You approved this invoice
          </p>
        )}

        {/* Actions */}
        {awaitingApproval && !invoice.participant_approved && (
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleApprove}
              disabled={loading}
              className={`flex-1 rounded-xl py-3 text-sm font-semibold text-white transition-colors disabled:opacity-50 ${
                confirming
                  ? 'bg-green-700'
                  : 'bg-green-600 hover:bg-green-700 active:bg-green-800'
              }`}
            >
              {loading ? 'Approving…' : confirming ? 'Tap again to confirm' : 'Approve'}
            </button>
            <button
              type="button"
              onClick={() => setQueryOpen(true)}
              className="flex-1 rounded-xl border border-gray-300 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 active:bg-gray-100"
            >
              Query
            </button>
          </div>
        )}

        {/* Cancel confirmation */}
        {confirming && !loading && (
          <button
            type="button"
            onClick={() => setConfirming(false)}
            className="mt-2 w-full text-center text-xs text-gray-400 underline"
          >
            Cancel
          </button>
        )}
      </div>

      {queryOpen && (
        <InvoiceQueryDialog
          invoiceId={invoice.id}
          onSubmit={async (msg) => {
            await onQuery(invoice.id, msg)
            setQueryOpen(false)
          }}
          onClose={() => setQueryOpen(false)}
        />
      )}
    </>
  )
}
