'use client'

import { useState } from 'react'
import { X, RefreshCw, AlertTriangle } from 'lucide-react'
import type { Invoice } from '@/lib/types/invoice'
import {
  approveInvoice,
  rejectInvoice,
  requestInfo,
  triggerValidation,
} from '@/lib/api/invoices'
import InvoiceStatusBadge from './InvoiceStatusBadge'
import OCRConfidenceBar from './OCRConfidenceBar'
import ValidationResultsPanel from './ValidationResultsPanel'
import ApproveDialog from './ApproveDialog'
import RejectDialog from './RejectDialog'
import RequestInfoDialog from './RequestInfoDialog'

interface InvoiceDetailModalProps {
  invoice: Invoice
  onClose: () => void
  onUpdated: (updated: Invoice) => void
}

export default function InvoiceDetailModal({
  invoice,
  onClose,
  onUpdated,
}: InvoiceDetailModalProps) {
  const [current, setCurrent] = useState<Invoice>(invoice)
  const [approveOpen, setApproveOpen] = useState(false)
  const [rejectOpen, setRejectOpen] = useState(false)
  const [requestOpen, setRequestOpen] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [revalidating, setRevalidating] = useState(false)

  async function handleApprove(notes: string) {
    setActionLoading(true)
    setActionError(null)
    try {
      const updated = await approveInvoice(current.id, notes)
      setCurrent(updated)
      onUpdated(updated)
      setApproveOpen(false)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to approve invoice')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleReject(reason: string) {
    setActionLoading(true)
    setActionError(null)
    try {
      const updated = await rejectInvoice(current.id, reason)
      setCurrent(updated)
      onUpdated(updated)
      setRejectOpen(false)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to reject invoice')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleRequestInfo(message: string) {
    setActionLoading(true)
    setActionError(null)
    try {
      const updated = await requestInfo(current.id, message)
      setCurrent(updated)
      onUpdated(updated)
      setRequestOpen(false)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to send request')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleRevalidate() {
    setRevalidating(true)
    setActionError(null)
    try {
      await triggerValidation(current.id)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Validation failed')
    } finally {
      setRevalidating(false)
    }
  }

  const pdfUrl = current.gcs_pdf_path
    ? `/api/v1/invoices/${current.id}/pdf`
    : null

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/40" onClick={onClose} />

      <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-3xl flex-col bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-gray-900">
              Invoice {current.invoice_number ?? current.id}
            </h2>
            <InvoiceStatusBadge status={current.status} />
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex flex-1 overflow-hidden">
          {/* PDF Preview */}
          <div className="flex w-1/2 flex-col border-r bg-gray-50">
            <div className="border-b px-4 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
              PDF Preview
            </div>
            {pdfUrl ? (
              <iframe
                src={pdfUrl}
                className="flex-1"
                title="Invoice PDF"
              />
            ) : (
              <div className="flex flex-1 items-center justify-center text-sm text-gray-400">
                No PDF available
              </div>
            )}
          </div>

          {/* Details panel */}
          <div className="flex w-1/2 flex-col overflow-y-auto">
            <div className="space-y-6 px-5 py-4">
              {/* OCR Confidence */}
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  OCR Confidence
                </p>
                <div className="flex items-center gap-2">
                  <OCRConfidenceBar confidence={current.ocr_confidence} />
                  {current.ocr_confidence != null &&
                    current.ocr_confidence < 0.85 && (
                      <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    )}
                </div>
              </div>

              {/* Extracted Fields */}
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Extracted Fields
                </p>
                <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  <dt className="text-gray-500">Provider ID</dt>
                  <dd className="font-medium text-gray-900">
                    {current.provider_id ?? '—'}
                  </dd>
                  <dt className="text-gray-500">Participant ID</dt>
                  <dd className="font-medium text-gray-900">
                    {current.participant_id ?? '—'}
                  </dd>
                  <dt className="text-gray-500">Invoice Date</dt>
                  <dd className="font-medium text-gray-900">
                    {current.invoice_date ?? '—'}
                  </dd>
                  <dt className="text-gray-500">Due Date</dt>
                  <dd className="font-medium text-gray-900">
                    {current.due_date ?? '—'}
                  </dd>
                  <dt className="text-gray-500">Total Amount</dt>
                  <dd className="font-medium text-gray-900">
                    ${current.total_amount}
                  </dd>
                  <dt className="text-gray-500">GST Amount</dt>
                  <dd className="font-medium text-gray-900">
                    ${current.gst_amount}
                  </dd>
                </dl>
              </div>

              {/* Line Items */}
              {current.line_items.length > 0 && (
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Line Items
                  </p>
                  <div className="overflow-x-auto rounded-md border">
                    <table className="min-w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">
                            Support Item
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">
                            Description
                          </th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                            Qty
                          </th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                            Unit Price
                          </th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                            Total
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {current.line_items.map((item) => (
                          <tr key={item.id}>
                            <td className="px-3 py-2 text-gray-700">
                              {item.support_item_number ?? '—'}
                            </td>
                            <td className="px-3 py-2 text-gray-700">
                              {item.description ?? '—'}
                            </td>
                            <td className="px-3 py-2 text-right text-gray-700">
                              {item.quantity}
                            </td>
                            <td className="px-3 py-2 text-right text-gray-700">
                              ${item.unit_price}
                            </td>
                            <td className="px-3 py-2 text-right font-medium text-gray-900">
                              ${item.total}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Validation Results */}
              {current.validation_results != null && (
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Validation Results
                  </p>
                  <ValidationResultsPanel results={current.validation_results} />
                </div>
              )}

              {/* Review Info */}
              {(current.reviewed_by ?? current.reviewed_at) && (
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Review History
                  </p>
                  <p className="text-sm text-gray-700">
                    Reviewed by{' '}
                    <span className="font-medium">{current.reviewed_by}</span>
                    {current.reviewed_at && (
                      <> on {new Date(current.reviewed_at).toLocaleString()}</>
                    )}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Actions footer */}
        <div className="border-t px-6 py-4">
          {actionError && (
            <p className="mb-3 text-sm text-red-600">{actionError}</p>
          )}
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => setApproveOpen(true)}
              disabled={actionLoading}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              ✅ Approve
            </button>
            <button
              type="button"
              onClick={() => setRejectOpen(true)}
              disabled={actionLoading}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              ❌ Reject
            </button>
            <button
              type="button"
              onClick={() => setRequestOpen(true)}
              disabled={actionLoading}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              💬 Request Info
            </button>
            <button
              type="button"
              onClick={handleRevalidate}
              disabled={revalidating}
              className="flex items-center gap-1 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${revalidating ? 'animate-spin' : ''}`} />
              Re-validate
            </button>
          </div>
        </div>
      </div>

      <ApproveDialog
        open={approveOpen}
        invoiceNumber={current.invoice_number}
        onConfirm={handleApprove}
        onCancel={() => setApproveOpen(false)}
        loading={actionLoading}
      />
      <RejectDialog
        open={rejectOpen}
        invoiceNumber={current.invoice_number}
        onConfirm={handleReject}
        onCancel={() => setRejectOpen(false)}
        loading={actionLoading}
      />
      <RequestInfoDialog
        open={requestOpen}
        invoiceNumber={current.invoice_number}
        onConfirm={handleRequestInfo}
        onCancel={() => setRequestOpen(false)}
        loading={actionLoading}
      />
    </>
  )
}
