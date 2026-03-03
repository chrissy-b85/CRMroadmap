'use client'

import { useState } from 'react'

interface ApproveDialogProps {
  open: boolean
  invoiceNumber: string | null
  onConfirm: (notes: string) => void
  onCancel: () => void
  loading?: boolean
}

export default function ApproveDialog({
  open,
  invoiceNumber,
  onConfirm,
  onCancel,
  loading = false,
}: ApproveDialogProps) {
  const [notes, setNotes] = useState('')

  if (!open) return null

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onConfirm(notes)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-gray-900">Approve Invoice</h2>
        <p className="mt-1 text-sm text-gray-500">
          Approve invoice{invoiceNumber ? ` #${invoiceNumber}` : ''}?
        </p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label
              htmlFor="approve-notes"
              className="block text-sm font-medium text-gray-700"
            >
              Notes <span className="text-gray-400">(optional)</span>
            </label>
            <textarea
              id="approve-notes"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
              placeholder="Add any approval notes…"
            />
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
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? 'Approving…' : '✅ Approve'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
