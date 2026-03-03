'use client'

import { useState } from 'react'

interface RequestInfoDialogProps {
  open: boolean
  invoiceNumber: string | null
  onConfirm: (message: string) => void
  onCancel: () => void
  loading?: boolean
}

export default function RequestInfoDialog({
  open,
  invoiceNumber,
  onConfirm,
  onCancel,
  loading = false,
}: RequestInfoDialogProps) {
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  if (!open) return null

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!message.trim()) {
      setError('A message is required.')
      return
    }
    setError('')
    onConfirm(message.trim())
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-gray-900">Request Information</h2>
        <p className="mt-1 text-sm text-gray-500">
          Send a request for more information about invoice
          {invoiceNumber ? ` #${invoiceNumber}` : ''} to the provider.
        </p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label
              htmlFor="info-message"
              className="block text-sm font-medium text-gray-700"
            >
              Message <span className="text-red-500">*</span>
            </label>
            <textarea
              id="info-message"
              rows={4}
              value={message}
              onChange={(e) => {
                setMessage(e.target.value)
                if (e.target.value.trim()) setError('')
              }}
              className={`mt-1 block w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-1 ${
                error
                  ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
              }`}
              placeholder="Describe what additional information is needed…"
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
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Sending…' : '💬 Send Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
