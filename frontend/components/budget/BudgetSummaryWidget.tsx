'use client'

import type { PlanBudgetSummary, SupportCategoryBudgetStatus } from '@/lib/types/budget'

interface BudgetSummaryWidgetProps {
  summary: PlanBudgetSummary
}

const alertColour: Record<string, string> = {
  overspent: 'bg-red-500',
  critical: 'bg-orange-400',
  warning: 'bg-yellow-400',
}

function utilisationColour(utilisation: number, isOverspent: boolean): string {
  if (isOverspent) return 'bg-red-500'
  if (utilisation >= 90) return 'bg-orange-400'
  if (utilisation >= 75) return 'bg-yellow-400'
  return 'bg-green-500'
}

function CategoryRow({ cat }: { cat: SupportCategoryBudgetStatus }) {
  const pct = Math.min(cat.utilisation_percent, 100)
  const barColour = utilisationColour(cat.utilisation_percent, cat.is_overspent)

  return (
    <div className="mb-4">
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="font-medium text-gray-800">{cat.ndis_support_category}</span>
        <span className="text-gray-500">
          ${Number(cat.budget_spent).toLocaleString()} /{' '}
          ${Number(cat.budget_allocated).toLocaleString()}
          {cat.alert_level && (
            <span
              className={`ml-2 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold text-white ${alertColour[cat.alert_level] ?? 'bg-gray-400'}`}
            >
              {cat.alert_level.toUpperCase()}
            </span>
          )}
        </span>
      </div>
      {/* Stacked bar: spent | remaining */}
      <div className="flex h-4 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className={`${barColour} h-full transition-all duration-300`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mt-0.5 flex justify-between text-xs text-gray-500">
        <span>{cat.utilisation_percent.toFixed(1)}% utilised</span>
        {cat.projected_exhaustion_date && (
          <span>Est. exhaustion: {cat.projected_exhaustion_date}</span>
        )}
      </div>
    </div>
  )
}

export default function BudgetSummaryWidget({ summary }: BudgetSummaryWidgetProps) {
  const overallPct = Math.min(summary.overall_utilisation_percent, 100)
  const overallColour = utilisationColour(summary.overall_utilisation_percent, false)

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <h3 className="mb-1 text-base font-semibold text-gray-900">Budget Summary</h3>
      <p className="mb-4 text-xs text-gray-500">
        Plan period: {summary.plan_start_date} → {summary.plan_end_date} &nbsp;|&nbsp;{' '}
        <span className={summary.days_remaining < 30 ? 'font-bold text-red-600' : ''}>
          {summary.days_remaining} day(s) remaining
        </span>
      </p>

      {/* Overall progress bar */}
      <div className="mb-1 flex justify-between text-sm text-gray-700">
        <span>Overall utilisation</span>
        <span>{summary.overall_utilisation_percent.toFixed(1)}%</span>
      </div>
      <div className="mb-1 flex h-5 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className={`${overallColour} h-full transition-all duration-300`}
          style={{ width: `${overallPct}%` }}
        />
      </div>
      <div className="mb-5 flex justify-between text-xs text-gray-500">
        <span>Spent: ${Number(summary.total_spent).toLocaleString()}</span>
        <span>Remaining: ${Number(summary.total_remaining).toLocaleString()}</span>
        <span>Total: ${Number(summary.total_allocated).toLocaleString()}</span>
      </div>

      {/* Per-category rows */}
      {summary.categories.map((cat) => (
        <CategoryRow key={cat.category_id} cat={cat} />
      ))}
    </div>
  )
}
