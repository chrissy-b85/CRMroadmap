import Link from 'next/link'
import { getMyBudgetSummary } from '@/lib/api/portal'
import PlanSummaryCard from '@/components/portal/PlanSummaryCard'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    maximumFractionDigits: 0,
  }).format(amount)
}

function getBudgetHealth(pct: number): { label: string; colour: string } {
  if (pct > 90) return { label: 'Critical', colour: 'bg-red-100 text-red-700 border-red-200' }
  if (pct >= 75) return { label: 'Warning', colour: 'bg-amber-100 text-amber-700 border-amber-200' }
  return { label: 'Healthy', colour: 'bg-green-100 text-green-700 border-green-200' }
}

async function getSummary() {
  try {
    return await getMyBudgetSummary()
  } catch {
    return null
  }
}

export default async function PortalHomePage() {
  const summary = await getSummary()

  if (!summary) {
    return (
      <div
        role="alert"
        className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700"
      >
        Unable to load your plan data. Please try again later.
      </div>
    )
  }

  const utilisationPct =
    summary.totalAllocated > 0
      ? Math.round((summary.totalSpent / summary.totalAllocated) * 100)
      : 0

  const { label: healthLabel, colour: healthColour } = getBudgetHealth(utilisationPct)

  return (
    <div className="space-y-5">
      {/* Welcome */}
      <section>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {summary.participantFirstName} 👋
        </h1>
        <p className="mt-1 text-sm text-gray-500">Here&apos;s your NDIS plan at a glance.</p>
      </section>

      {/* Budget health indicator */}
      <div
        className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-medium ${healthColour}`}
      >
        <span aria-hidden="true">
          {utilisationPct > 90 ? '🔴' : utilisationPct >= 75 ? '🟡' : '🟢'}
        </span>
        Budget Health: {healthLabel}
      </div>

      {/* Plan summary card */}
      <PlanSummaryCard
        planStartDate={summary.planStartDate}
        planEndDate={summary.planEndDate}
        totalAllocated={summary.totalAllocated}
        totalSpent={summary.totalSpent}
      />

      {/* Quick stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl bg-blue-50 p-4 shadow-sm">
          <p className="text-xs font-medium text-blue-600">Budget Remaining</p>
          <p className="mt-1 text-2xl font-bold text-blue-700">
            {formatCurrency(summary.totalAllocated - summary.totalSpent)}
          </p>
        </div>
        <div className="rounded-xl bg-yellow-50 p-4 shadow-sm">
          <p className="text-xs font-medium text-yellow-600">Pending Invoices</p>
          <p className="mt-1 text-2xl font-bold text-yellow-700">
            {summary.pendingInvoicesCount}
          </p>
        </div>
      </div>

      {/* Quick links */}
      <div className="flex gap-3">
        <Link
          href="/portal/budget"
          className="flex-1 rounded-lg bg-blue-600 px-4 py-3 text-center text-sm font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          View Budget
        </Link>
        <Link
          href="/portal/invoices"
          className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-3 text-center text-sm font-semibold text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          View Invoices
        </Link>
      </div>
    </div>
  )
}
