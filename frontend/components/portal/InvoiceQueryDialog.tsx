'use client'

import { useState } from 'react'

const MAX_CHARS = 500

interface InvoiceQueryDialogProps {
  invoiceId: string
  onSubmit: (message: string) => Promise<void>
  onClose: () => void
}

export default function InvoiceQueryDialog({
  invoiceId,
  onSubmit,
  onClose,
}: InvoiceQueryDialogProps) {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const remaining = MAX_CHARS - message.length
  const canSubmit = message.trim().length > 0 && remaining >= 0

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!canSubmit) return
    setLoading(true)
    setError(null)
    try {
      await onSubmit(message.trim())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send query')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="query-dialog-title"
        className="fixed inset-x-4 top-1/2 z-50 -translate-y-1/2 rounded-2xl bg-white p-5 shadow-2xl sm:inset-x-auto sm:left-1/2 sm:w-full sm:max-w-md sm:-translate-x-1/2"
      >
        <h2
          id="query-dialog-title"
          className="mb-1 text-base font-bold text-gray-900"
        >
          Query Invoice
        </h2>
        <p className="mb-4 text-sm text-gray-500">
          Describe what you&apos;d like clarified about this invoice.
        </p>

        <form onSubmit={handleSubmit}>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value.slice(0, MAX_CHARS))}
            rows={5}
            placeholder="e.g. The hourly rate on line 2 doesn't match my service agreement…"
            className="w-full resize-none rounded-xl border border-gray-300 px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />

          <div className="mt-1 flex justify-end">
            <span
              className={`text-xs ${remaining < 50 ? 'text-red-500' : 'text-gray-400'}`}
            >
              {remaining} characters remaining
            </span>
          </div>

          {error && (
            <p className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          <div className="mt-4 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-xl border border-gray-300 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSubmit || loading}
              className="flex-1 rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Sending…' : 'Send Query'}
            </button>
          </div>
        </form>
      </div>
    </>
  )
}
