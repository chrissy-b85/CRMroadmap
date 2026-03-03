import '@testing-library/jest-dom'
import React from 'react'
import { render, screen } from '@testing-library/react'
import InvoiceStatusBadge from '@/components/invoices/InvoiceStatusBadge'
import type { InvoiceStatus } from '@/lib/types/invoice'

const cases: Array<{ status: InvoiceStatus; label: string; colourClass: string }> = [
  { status: 'queued', label: 'Queued', colourClass: 'bg-blue-100' },
  { status: 'flagged', label: 'Flagged', colourClass: 'bg-red-100' },
  { status: 'pending_approval', label: 'Pending Approval', colourClass: 'bg-yellow-100' },
  { status: 'info_requested', label: 'Info Requested', colourClass: 'bg-orange-100' },
  { status: 'approved', label: 'Approved', colourClass: 'bg-green-100' },
  { status: 'rejected', label: 'Rejected', colourClass: 'bg-gray-100' },
  { status: 'paid', label: 'Paid', colourClass: 'bg-purple-100' },
]

describe('InvoiceStatusBadge', () => {
  test.each(cases)(
    'renders "$label" with colour class "$colourClass" for status "$status"',
    ({ status, label, colourClass }) => {
      const { container } = render(<InvoiceStatusBadge status={status} />)
      const badge = screen.getByText(label)
      expect(badge).toBeInTheDocument()
      expect(badge.className).toContain(colourClass)
    }
  )
})
