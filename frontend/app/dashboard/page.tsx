import Link from 'next/link'
import { getDashboardSummary, getInvoiceStatusSummary, getSpendOverTime } from '@/lib/api/reports'
import { KPICard } from '@/components/reports/KPICard'
import { SpendOverTimeChart } from '@/components/reports/SpendOverTimeChart'
import { InvoiceStatusDonut } from '@/components/reports/InvoiceStatusDonut'

function formatCurrency(value: string | null): string {
  if (value === null) return '—'
  const num = parseFloat(value)
  if (isNaN(num)) return '—'
  return new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD', maximumFractionDigits: 0 }).format(num)
}

export default async function DashboardPage() {
  const [summary, statusSummary, spendOverTime] = await Promise.all([
    getDashboardSummary().catch(() => null),
    getInvoiceStatusSummary().catch(() => null),
    getSpendOverTime({ granularity: 'month' }).catch(() => []),
  ])

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <Link
            href="/dashboard/reports"
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            📊 Reports
          </Link>
        </div>

        {/* Row 1: Participant & Plan KPIs */}
        <section className="mb-6">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <KPICard
              title="Active Participants"
              value={summary?.active_participants ?? null}
              icon="👥"
              href="/dashboard/participants"
              variant="default"
            />
            <KPICard
              title="Active Plans"
              value={summary?.active_plans ?? null}
              icon="📋"
              href="/dashboard/plans"
              variant="default"
            />
            <KPICard
              title="Pending Approvals"
              value={summary?.pending_approvals ?? null}
              icon="⚠️"
              href="/dashboard/invoices?status=PENDING_APPROVAL"
              variant={(summary?.pending_approvals ?? 0) > 0 ? 'warning' : 'default'}
            />
            <KPICard
              title="Flagged Invoices"
              value={summary?.flagged_invoices ?? null}
              icon="🚨"
              href="/dashboard/invoices?status=FLAGGED"
              variant={(summary?.flagged_invoices ?? 0) > 0 ? 'danger' : 'default'}
            />
          </div>
        </section>

        {/* Row 2: Financial KPIs */}
        <section className="mb-10">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <KPICard
              title="Total Spend This Month"
              value={formatCurrency(summary?.total_spend_this_month ?? null)}
              icon="💰"
              variant="info"
            />
            <KPICard
              title="Budget Under Management"
              value={formatCurrency(summary?.total_budget_under_management ?? null)}
              icon="📊"
              variant="info"
            />
            <KPICard
              title="Plans Expiring in 30 Days"
              value={summary?.plans_expiring_30_days ?? null}
              icon="⏰"
              href="/dashboard/plans?expiring=30"
              variant={(summary?.plans_expiring_30_days ?? 0) > 0 ? 'warning' : 'default'}
            />
            <KPICard
              title="Critical Budget Alerts"
              value={summary?.critical_budget_alerts ?? null}
              icon="🔔"
              href="/dashboard/budget/alerts?severity=critical"
              variant={(summary?.critical_budget_alerts ?? 0) > 0 ? 'danger' : 'default'}
            />
          </div>
        </section>

        {/* Charts Row */}
        <section>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Spend Over Time */}
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-gray-800">Spend Over Time</h2>
              {spendOverTime.length > 0 ? (
                <SpendOverTimeChart data={spendOverTime} />
              ) : (
                <p className="py-10 text-center text-sm text-gray-400">No spend data available</p>
              )}
            </div>

            {/* Invoice Status Distribution */}
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-gray-800">
                Invoice Status Distribution
              </h2>
              {statusSummary ? (
                <InvoiceStatusDonut data={statusSummary} />
              ) : (
                <p className="py-10 text-center text-sm text-gray-400">No invoice data available</p>
              )}
            </div>
          </div>
        </section>

        {/* Quick Actions */}
        <section className="mt-10">
          <h2 className="mb-4 text-lg font-semibold text-gray-700">Quick Actions</h2>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/dashboard/invoices"
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              View Invoice Queue
            </Link>
            <Link
              href="/dashboard/reports"
              className="rounded-md bg-gray-600 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
            >
              Full Reports
            </Link>
          </div>
        </section>
      </div>
    </main>
  )
}

