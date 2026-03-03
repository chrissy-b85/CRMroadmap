import Link from 'next/link'
import { getAllBudgetAlerts } from '@/lib/api/budget'
import { getInvoices } from '@/lib/api/invoices'

async function getInvoiceStats() {
  try {
    const [flagged, pending, approved] = await Promise.all([
      getInvoices({ status: 'flagged', pageSize: 1 }),
      getInvoices({ status: 'pending_approval', pageSize: 1 }),
      getInvoices({ status: 'approved', pageSize: 1 }),
    ])
    return {
      flaggedCount: flagged.total,
      pendingCount: pending.total,
      approvedCount: approved.total,
    }
  } catch {
    return { flaggedCount: null, pendingCount: null, approvedCount: null }
  }
}

async function getBudgetAlertStats() {
  try {
    const alerts = await getAllBudgetAlerts()
    const criticalCount = alerts.filter((a) => a.severity === 'critical').length
    const warningCount = alerts.filter((a) => a.severity === 'warning').length
    const expiringCount = alerts.filter((a) => a.alert_type === 'PLAN_EXPIRING').length
    return { criticalCount, warningCount, expiringCount }
  } catch {
    return { criticalCount: null, warningCount: null, expiringCount: null }
  }
}

export default async function DashboardPage() {
  const { flaggedCount, pendingCount, approvedCount } = await getInvoiceStats()
  const { criticalCount, warningCount, expiringCount } = await getBudgetAlertStats()

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <h1 className="mb-8 text-2xl font-bold text-gray-900">Dashboard</h1>

        {/* Invoice Stats */}
        <section>
          <h2 className="mb-4 text-lg font-semibold text-gray-700">
            Invoice Overview
          </h2>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {/* Flagged */}
            <Link
              href="/dashboard/invoices?status=flagged"
              className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50 p-5 shadow-sm transition hover:shadow-md"
            >
              <div>
                <p className="text-sm font-medium text-red-700">
                  Flagged Invoices
                </p>
                <p className="mt-1 text-3xl font-bold text-red-900">
                  {flaggedCount ?? '—'}
                </p>
              </div>
              <span className="text-3xl">🚩</span>
            </Link>

            {/* Pending Approval */}
            <Link
              href="/dashboard/invoices?status=pending_approval"
              className="flex items-center justify-between rounded-lg border border-yellow-200 bg-yellow-50 p-5 shadow-sm transition hover:shadow-md"
            >
              <div>
                <p className="text-sm font-medium text-yellow-700">
                  Pending Approval
                </p>
                <p className="mt-1 text-3xl font-bold text-yellow-900">
                  {pendingCount ?? '—'}
                </p>
              </div>
              <span className="text-3xl">⏳</span>
            </Link>

            {/* Approved Today */}
            <Link
              href="/dashboard/invoices?status=approved"
              className="flex items-center justify-between rounded-lg border border-green-200 bg-green-50 p-5 shadow-sm transition hover:shadow-md"
            >
              <div>
                <p className="text-sm font-medium text-green-700">
                  Approved Invoices
                </p>
                <p className="mt-1 text-3xl font-bold text-green-900">
                  {approvedCount ?? '—'}
                </p>
              </div>
              <span className="text-3xl">✅</span>
            </Link>
          </div>
        </section>

        {/* Quick links */}
        <section className="mt-10">
          <h2 className="mb-4 text-lg font-semibold text-gray-700">
            Quick Actions
          </h2>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/dashboard/invoices"
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              View Invoice Queue
            </Link>
          </div>
        </section>

        {/* Budget Health */}
        <section className="mt-10">
          <h2 className="mb-4 text-lg font-semibold text-gray-700">
            Budget Health
          </h2>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {/* Critical alerts */}
            <Link
              href="/dashboard/budget/alerts?severity=critical"
              className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50 p-5 shadow-sm transition hover:shadow-md"
            >
              <div>
                <p className="text-sm font-medium text-red-700">
                  Critical Budget Alerts
                </p>
                <p className="mt-1 text-3xl font-bold text-red-900">
                  {criticalCount ?? '—'}
                </p>
              </div>
              <span className="text-3xl">🔴</span>
            </Link>

            {/* Warning alerts */}
            <Link
              href="/dashboard/budget/alerts?severity=warning"
              className="flex items-center justify-between rounded-lg border border-yellow-200 bg-yellow-50 p-5 shadow-sm transition hover:shadow-md"
            >
              <div>
                <p className="text-sm font-medium text-yellow-700">
                  Warning Budget Alerts
                </p>
                <p className="mt-1 text-3xl font-bold text-yellow-900">
                  {warningCount ?? '—'}
                </p>
              </div>
              <span className="text-3xl">🟡</span>
            </Link>

            {/* Plans expiring */}
            <div className="flex items-center justify-between rounded-lg border border-orange-200 bg-orange-50 p-5 shadow-sm">
              <div>
                <p className="text-sm font-medium text-orange-700">
                  Plans Expiring ({'<'} 30 days)
                </p>
                <p className="mt-1 text-3xl font-bold text-orange-900">
                  {expiringCount ?? '—'}
                </p>
              </div>
              <span className="text-3xl">📅</span>
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
