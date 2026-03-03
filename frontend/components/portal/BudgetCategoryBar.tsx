'use client'

import type { BudgetAlertLevel } from '@/lib/types/portal'

export interface BudgetCategoryBarProps {
  categoryName: string
  spent: number
  allocated: number
  alertLevel?: BudgetAlertLevel
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    maximumFractionDigits: 0,
  }).format(amount)
}

function getBarColour(pct: number, alertLevel?: BudgetAlertLevel): string {
  if (alertLevel === 'overspent') return 'bg-red-600'
  if (pct > 90 || alertLevel === 'critical') return 'bg-red-500'
  if (pct >= 75 || alertLevel === 'warning') return 'bg-amber-400'
  return 'bg-green-500'
}

function getTextColour(pct: number, alertLevel?: BudgetAlertLevel): string {
  if (alertLevel === 'overspent') return 'text-red-700'
  if (pct > 90 || alertLevel === 'critical') return 'text-red-600'
  if (pct >= 75 || alertLevel === 'warning') return 'text-amber-600'
  return 'text-green-600'
}

export default function BudgetCategoryBar({
  categoryName,
  spent,
  allocated,
  alertLevel,
}: BudgetCategoryBarProps) {
  const pct = allocated > 0 ? Math.min((spent / allocated) * 100, 100) : 0
  const pctDisplay = Math.round(pct)
  const remaining = allocated - spent
  const barColour = getBarColour(pct, alertLevel)
  const textColour = getTextColour(pct, alertLevel)

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">{categoryName}</span>
        <span className={`text-sm font-semibold ${textColour}`}>
          {pctDisplay}%
        </span>
      </div>

      <div
        role="progressbar"
        aria-label={`${categoryName} budget usage`}
        aria-valuenow={pctDisplay}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-3 w-full overflow-hidden rounded-full bg-gray-200"
      >
        <div
          className={`h-full rounded-full transition-all duration-300 ${barColour}`}
          style={{ width: `${pctDisplay}%` }}
        />
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>
          Spent: <span className="font-medium text-gray-700">{formatCurrency(spent)}</span>
          {' / '}
          <span className="font-medium text-gray-700">{formatCurrency(allocated)}</span>
        </span>
        <span>
          Remaining:{' '}
          <span className="font-bold text-gray-800">{formatCurrency(remaining)}</span>
        </span>
      </div>
    </div>
  )
}
