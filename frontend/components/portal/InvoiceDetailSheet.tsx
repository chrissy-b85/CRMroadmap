'use client'

import { useState } from 'react'
import type { Invoice } from '@/lib/types/invoice'
import { participantApproveInvoice, participantQueryInvoice } from '@/lib/api/portal'
import InvoiceQueryDialog from './InvoiceQueryDialog'

interface InvoiceDetailSheetProps {
  invoice: Invoice
  onClose: () => void
  onUpdated: (invoice: Invoice) => void
}

export default function InvoiceDetailSheet({
  invoice,
  onClose,
  onUpdated,
}: InvoiceDetailSheetProps) {
  const [queryOpen, setQueryOpen] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const awaitingApproval =
    invoice.status.toLowerCase() === 'pending_approval'

  async function handleApprove() {
    if (!confirming) {
      setConfirming(true)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const updated = await participantApproveInvoice(invoice.id)
      onUpdated(updated)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Approval failed')
    } finally {
      setLoading(false)
      setConfirming(false)
    }
  }

  async function handleQuery(message: string) {
    setLoading(true)
    setError(null)
    try {
      const updated = await participantQueryInvoice(invoice.id, message)
      onUpdated(updated)
      setQueryOpen(false)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-up sheet */}
      <div className="fixed inset-x-0 bottom-0 z-50 max-h-[90vh] overflow-y-auto rounded-t-2xl bg-white pb-safe shadow-xl">
        {/* Drag handle */}
        <div className="mx-auto mt-3 h-1 w-10 rounded-full bg-gray-300" />

        <div className="p-5">
          {/* Title */}
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900">
              {invoice.invoice_number ?? `Invoice ${invoice.id.slice(0, 8)}`}
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full p-1 text-gray-400 hover:bg-gray-100"
              aria-label="Close"
            >
              ✕
            </button>
          </div>

          {/* PDF preview */}
          {invoice.gcs_pdf_path ? (
            <div className="mb-4 overflow-hidden rounded-xl border border-gray-200 bg-gray-50">
              <iframe
                src={invoice.gcs_pdf_path}
                title="Invoice PDF"
                className="h-64 w-full"
              />
            </div>
          ) : (
            <div className="mb-4 flex h-32 items-center justify-center rounded-xl border border-dashed border-gray-300 text-sm text-gray-400">
              PDF not available
            </div>
          )}

          {/* Key fields */}
          <dl className="mb-4 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs text-gray-500">Provider</dt>
              <dd className="font-medium text-gray-900">{invoice.provider_id ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Date</dt>
              <dd className="font-medium text-gray-900">{invoice.invoice_date ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Total</dt>
              <dd className="text-2xl font-bold text-gray-900">
                ${parseFloat(invoice.total_amount).toFixed(2)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">GST</dt>
              <dd className="font-medium text-gray-900">
                ${parseFloat(invoice.gst_amount).toFixed(2)}
              </dd>
            </div>
          </dl>

          {/* Line items */}
          {invoice.line_items.length > 0 && (
            <div className="mb-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Line Items
              </h3>
              <ul className="divide-y divide-gray-100 rounded-xl border border-gray-200">
                {invoice.line_items.map((item) => (
                  <li key={item.id} className="px-3 py-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-800">{item.description ?? '—'}</span>
                      <span className="font-medium text-gray-900">
                        ${parseFloat(item.total).toFixed(2)}
                      </span>
                    </div>
                    {item.support_item_number && (
                      <span className="mt-0.5 inline-block rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
                        {item.support_item_number}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Error */}
          {error && (
            <p className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          {/* Actions */}
          {awaitingApproval && !invoice.participant_approved && (
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleApprove}
                disabled={loading}
                className={`flex-1 rounded-xl py-3.5 text-sm font-semibold text-white disabled:opacity-50 ${
                  confirming ? 'bg-green-700' : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                {loading ? 'Approving…' : confirming ? 'Confirm Approve' : 'Approve'}
              </button>
              <button
                type="button"
                onClick={() => setQueryOpen(true)}
                className="flex-1 rounded-xl border border-gray-300 py-3.5 text-sm font-semibold text-gray-700 hover:bg-gray-50"
              >
                Query
              </button>
            </div>
          )}

          {confirming && !loading && (
            <button
              type="button"
              onClick={() => setConfirming(false)}
              className="mt-2 w-full text-center text-xs text-gray-400 underline"
            >
              Cancel
            </button>
          )}

          {invoice.participant_approved && (
            <p className="rounded-xl bg-green-50 py-3 text-center text-sm font-medium text-green-700">
              ✓ You have approved this invoice
            </p>
          )}
        </div>
      </div>

      {queryOpen && (
        <InvoiceQueryDialog
          invoiceId={invoice.id}
          onSubmit={handleQuery}
          onClose={() => setQueryOpen(false)}
        />
      )}
    </>
  )
}
