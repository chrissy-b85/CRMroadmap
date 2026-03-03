import '@testing-library/jest-dom'
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import InvoiceApprovalCard from '@/components/portal/InvoiceApprovalCard'
import type { Invoice } from '@/lib/types/invoice'

jest.mock('@/lib/api/portal', () => ({
  participantApproveInvoice: jest.fn(),
}))

const baseInvoice: Invoice = {
  id: 'invoice-abc-123',
  participant_id: 'participant-1',
  provider_id: 'provider-1',
  invoice_number: 'INV-2024-001',
  invoice_date: '2024-07-01',
  due_date: '2024-07-31',
  total_amount: '1100.00',
  gst_amount: '100.00',
  status: 'pending_approval',
  ocr_confidence: 0.95,
  gcs_pdf_path: 'gs://bucket/test.pdf',
  line_items: [],
  validation_results: null,
  reviewed_by: null,
  reviewed_at: null,
  created_at: '2024-07-01T00:00:00Z',
  participant_approved: false,
  participant_approved_at: null,
  participant_query_message: null,
}

describe('InvoiceApprovalCard', () => {
  test('renders invoice number and amount', () => {
    render(
      <InvoiceApprovalCard
        invoice={baseInvoice}
        onApprove={jest.fn()}
        onQuery={jest.fn()}
      />
    )
    expect(screen.getByText('INV-2024-001')).toBeInTheDocument()
    expect(screen.getByText('$1100.00')).toBeInTheDocument()
  })

  test('calls onApprove after two taps when invoice is PENDING_APPROVAL', async () => {
    const pendingInvoice: Invoice = {
      ...baseInvoice,
      status: 'pending_approval',
    }
    const handleApprove = jest.fn().mockResolvedValue(undefined)
    render(
      <InvoiceApprovalCard
        invoice={pendingInvoice}
        onApprove={handleApprove}
        onQuery={jest.fn()}
      />
    )

    // First tap sets confirming state
    const approveBtn = screen.getByRole('button', { name: /approve/i })
    fireEvent.click(approveBtn)

    // Second tap confirms
    const confirmBtn = screen.getByRole('button', { name: /tap again to confirm/i })
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(handleApprove).toHaveBeenCalledWith(pendingInvoice.id)
    })
  })
})
