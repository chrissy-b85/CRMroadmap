import Link from 'next/link'
import { getMyBudgetHistory } from '@/lib/api/portal'

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

async function getHistory() {
  try {
    return await getMyBudgetHistory()
  } catch {
    return null
  }
}

export default async function BudgetHistoryPage() {
  const plans = await getHistory()

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <Link
          href="/portal/budget"
          aria-label="Back to Budget Overview"
          className="rounded-md p-1 text-gray-500 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          ← Back
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Budget History</h1>
      </div>

      {!plans ? (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700"
        >
          Unable to load budget history. Please try again later.
        </div>
      ) : plans.length === 0 ? (
        <p className="text-sm text-gray-500">No previous plans found.</p>
      ) : (
        <ol aria-label="Past plans" className="relative border-l border-gray-200 pl-6 space-y-6">
          {plans.map((plan) => (
            <li key={plan.planId} className="relative">
              {/* Timeline dot */}
              <span
                aria-hidden="true"
                className="absolute -left-3 flex h-5 w-5 items-center justify-center rounded-full bg-blue-100 ring-4 ring-white"
              >
                <span className="h-2.5 w-2.5 rounded-full bg-blue-600" />
              </span>

              <div className="rounded-xl bg-white p-4 shadow-sm">
                <p className="text-xs text-gray-400">
                  {formatDate(plan.planStartDate)} – {formatDate(plan.planEndDate)}
                </p>

                <div className="mt-2 flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500">Total Funding</p>
                    <p className="text-base font-semibold text-gray-800">
                      {formatCurrency(plan.totalAllocated)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">Spent</p>
                    <p className="text-base font-semibold text-gray-800">
                      {formatCurrency(plan.totalSpent)}
                    </p>
                  </div>
                </div>

                {/* Utilisation bar */}
                <div className="mt-3">
                  <div className="mb-1 flex justify-between text-xs text-gray-500">
                    <span>Utilisation</span>
                    <span className="font-medium">
                      {Math.round(plan.finalUtilisationPercent)}%
                    </span>
                  </div>
                  <div
                    role="progressbar"
                    aria-label={`Plan ${plan.planId} utilisation`}
                    aria-valuenow={Math.round(plan.finalUtilisationPercent)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    className="h-2.5 w-full overflow-hidden rounded-full bg-gray-200"
                  >
                    <div
                      className={`h-full rounded-full ${
                        plan.finalUtilisationPercent > 90
                          ? 'bg-red-400'
                          : plan.finalUtilisationPercent >= 75
                            ? 'bg-amber-400'
                            : 'bg-green-500'
                      }`}
                      style={{ width: `${Math.min(plan.finalUtilisationPercent, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
