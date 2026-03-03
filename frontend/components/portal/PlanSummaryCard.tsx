'use client'

interface PlanSummaryCardProps {
  planStartDate: string
  planEndDate: string
  totalAllocated: number
  totalSpent: number
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    maximumFractionDigits: 0,
  }).format(amount)
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-AU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function getDaysRemaining(endDate: string): number {
  const end = new Date(endDate)
  const now = new Date()
  const diff = end.getTime() - now.getTime()
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)))
}

export default function PlanSummaryCard({
  planStartDate,
  planEndDate,
  totalAllocated,
  totalSpent,
}: PlanSummaryCardProps) {
  const utilisationPct =
    totalAllocated > 0
      ? Math.min(Math.round((totalSpent / totalAllocated) * 100), 100)
      : 0
  const remaining = totalAllocated - totalSpent
  const daysRemaining = getDaysRemaining(planEndDate)

  // SVG ring chart values
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const spentOffset = circumference * (1 - utilisationPct / 100)

  return (
    <div className="rounded-2xl bg-white p-5 shadow-md">
      <h2 className="mb-4 text-base font-semibold text-gray-800">Plan Summary</h2>

      <div className="flex items-center gap-6">
        {/* Ring chart */}
        <div className="relative flex-shrink-0" aria-hidden="true">
          <svg width="128" height="128" viewBox="0 0 128 128">
            {/* Track */}
            <circle
              cx="64"
              cy="64"
              r={radius}
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="14"
            />
            {/* Progress */}
            <circle
              cx="64"
              cy="64"
              r={radius}
              fill="none"
              stroke={utilisationPct > 90 ? '#ef4444' : utilisationPct >= 75 ? '#f59e0b' : '#22c55e'}
              strokeWidth="14"
              strokeDasharray={circumference}
              strokeDashoffset={spentOffset}
              strokeLinecap="round"
              transform="rotate(-90 64 64)"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-xl font-bold text-gray-900">{utilisationPct}%</span>
            <span className="text-xs text-gray-500">used</span>
          </div>
        </div>

        {/* Stats */}
        <div className="min-w-0 flex-1 space-y-2">
          <div>
            <p className="text-xs text-gray-500">Total Funding</p>
            <p className="text-lg font-bold text-gray-900">{formatCurrency(totalAllocated)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Remaining</p>
            <p className="text-lg font-bold text-blue-600">{formatCurrency(remaining)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Days Remaining</p>
            <p className="text-base font-semibold text-gray-700">
              {daysRemaining} day{daysRemaining !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </div>

      {/* Plan period */}
      <p className="mt-4 text-center text-xs text-gray-400">
        Plan period: {formatDate(planStartDate)} – {formatDate(planEndDate)}
      </p>
    </div>
  )
}
