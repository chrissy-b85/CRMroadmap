'use client'

import { useState } from 'react'

interface RejectDialogProps {
  open: boolean
  invoiceNumber: string | null
  onConfirm: (reason: string) => void
  onCancel: () => void
  loading?: boolean
}

export default function RejectDialog({
  open,
  invoiceNumber,
  onConfirm,
  onCancel,
  loading = false,
}: RejectDialogProps) {
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')

  if (!open) return null

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!reason.trim()) {
      setError('A rejection reason is required.')
      return
    }
    setError('')
    onConfirm(reason.trim())
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-gray-900">Reject Invoice</h2>
        <p className="mt-1 text-sm text-gray-500">
          Reject invoice{invoiceNumber ? ` #${invoiceNumber}` : ''}? This action
          cannot be undone.
        </p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label
              htmlFor="reject-reason"
              className="block text-sm font-medium text-gray-700"
            >
              Reason <span className="text-red-500">*</span>
            </label>
            <textarea
              id="reject-reason"
              rows={3}
              value={reason}
              onChange={(e) => {
                setReason(e.target.value)
                if (e.target.value.trim()) setError('')
              }}
              className={`mt-1 block w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-1 ${
                error
                  ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:border-red-500 focus:ring-red-500'
              }`}
              placeholder="Enter the reason for rejection…"
            />
            {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onCancel}
              disabled={loading}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              {loading ? 'Rejecting…' : '❌ Reject'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
