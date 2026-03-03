import { getMyBudgetSummary } from '@/lib/api/portal'
import BudgetCategoryBar from '@/components/portal/BudgetCategoryBar'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    maximumFractionDigits: 0,
  }).format(amount)
}

function getDaysRemaining(endDate: string): number {
  const end = new Date(endDate)
  const now = new Date()
  const diff = end.getTime() - now.getTime()
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)))
}

async function getSummary() {
  try {
    return await getMyBudgetSummary()
  } catch {
    return null
  }
}

export default async function BudgetPage() {
  const summary = await getSummary()

  if (!summary) {
    return (
      <div
        role="alert"
        className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700"
      >
        Unable to load budget data. Please try again later.
      </div>
    )
  }

  const utilisationPct =
    summary.totalAllocated > 0
      ? Math.min(Math.round((summary.totalSpent / summary.totalAllocated) * 100), 100)
      : 0
  const daysRemaining = getDaysRemaining(summary.planEndDate)

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Budget Overview</h1>

      {/* Alert banners */}
      {summary.alerts.length > 0 && (
        <section aria-label="Budget alerts" className="space-y-2">
          {summary.alerts.map((alert) => (
            <div
              key={alert.id}
              role="alert"
              className={`rounded-lg border px-4 py-3 text-sm font-medium ${
                alert.level === 'critical'
                  ? 'border-red-200 bg-red-50 text-red-700'
                  : 'border-amber-200 bg-amber-50 text-amber-700'
              }`}
            >
              {alert.level === 'critical' ? '🔴' : '🟡'} {alert.message}
            </div>
          ))}
        </section>
      )}

      {/* Overall plan progress */}
      <div className="rounded-xl bg-white p-5 shadow-sm">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700">Overall Plan Progress</h2>
          <span className="text-sm font-bold text-gray-900">{utilisationPct}%</span>
        </div>
        <div
          role="progressbar"
          aria-label="Overall plan budget usage"
          aria-valuenow={utilisationPct}
          aria-valuemin={0}
          aria-valuemax={100}
          className="h-4 w-full overflow-hidden rounded-full bg-gray-200"
        >
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              utilisationPct > 90
                ? 'bg-red-500'
                : utilisationPct >= 75
                  ? 'bg-amber-400'
                  : 'bg-green-500'
            }`}
            style={{ width: `${utilisationPct}%` }}
          />
        </div>
        <div className="mt-2 flex justify-between text-xs text-gray-500">
          <span>
            Spent: <span className="font-semibold text-gray-700">{formatCurrency(summary.totalSpent)}</span>
          </span>
          <span>
            Total: <span className="font-semibold text-gray-700">{formatCurrency(summary.totalAllocated)}</span>
          </span>
        </div>
      </div>

      {/* Days remaining */}
      <div className="flex items-center gap-3 rounded-xl bg-blue-50 p-4 shadow-sm">
        <span className="text-3xl" aria-hidden="true">📅</span>
        <div>
          <p className="text-xs font-medium text-blue-600">Days Remaining in Plan</p>
          <p className="text-2xl font-bold text-blue-700">
            {daysRemaining} day{daysRemaining !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Per-category breakdown */}
      <section aria-label="Budget by support category">
        <h2 className="mb-3 text-base font-semibold text-gray-800">Support Categories</h2>
        <div className="space-y-4">
          {summary.categories.map((cat) => (
            <div key={cat.id} className="rounded-xl bg-white p-4 shadow-sm">
              <div className="mb-3 flex items-center gap-2">
                <span className="text-xl" aria-hidden="true">{cat.icon}</span>
                <h3 className="text-sm font-semibold text-gray-800">{cat.name}</h3>
              </div>

              <BudgetCategoryBar
                categoryName={cat.name}
                spent={cat.spent}
                allocated={cat.allocated}
                alertLevel={cat.alertLevel}
              />

              {cat.projectedExhaustionDate && (
                <p className="mt-2 text-xs text-gray-400">
                  Projected exhaustion:{' '}
                  <span className="font-medium text-gray-600">
                    {new Date(cat.projectedExhaustionDate).toLocaleDateString('en-AU', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    })}
                  </span>
                </p>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
