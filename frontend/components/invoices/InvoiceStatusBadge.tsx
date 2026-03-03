import type { InvoiceStatus } from '@/lib/types/invoice'

interface InvoiceStatusBadgeProps {
  status: InvoiceStatus
}

const statusConfig: Record<
  InvoiceStatus,
  { label: string; className: string }
> = {
  queued: {
    label: 'Queued',
    className: 'bg-blue-100 text-blue-800',
  },
  flagged: {
    label: 'Flagged',
    className: 'bg-red-100 text-red-800',
  },
  pending_approval: {
    label: 'Pending Approval',
    className: 'bg-yellow-100 text-yellow-800',
  },
  info_requested: {
    label: 'Info Requested',
    className: 'bg-orange-100 text-orange-800',
  },
  approved: {
    label: 'Approved',
    className: 'bg-green-100 text-green-800',
  },
  rejected: {
    label: 'Rejected',
    className: 'bg-gray-100 text-gray-700',
  },
  paid: {
    label: 'Paid',
    className: 'bg-purple-100 text-purple-800',
  },
}

export default function InvoiceStatusBadge({ status }: InvoiceStatusBadgeProps) {
  const config = statusConfig[status]
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${config.className}`}
    >
      {config.label}
    </span>
  )
}
