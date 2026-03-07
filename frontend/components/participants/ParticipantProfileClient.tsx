"use client";

import { useState } from 'react'
import Link from 'next/link'
import { AlertTriangle } from 'lucide-react'
import type {
  AuditLogEntry,
  Participant,
  ParticipantStatus,
  Plan,
  SupportCategory,
} from '@/lib/types/participant'

type Tab = 'overview' | 'plans' | 'audit'

function StatusBadge({ status }: { status: ParticipantStatus }) {
  const classes: Record<ParticipantStatus, string> = {
    active: 'bg-green-100 text-green-800',
    inactive: 'bg-gray-100 text-gray-800',
    plan_review_pending: 'bg-yellow-100 text-yellow-800',
  }
  const labels: Record<ParticipantStatus, string> = {
    active: 'Active',
    inactive: 'Inactive',
    plan_review_pending: 'Plan Review Pending',
  }
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${classes[status]}`}
    >
      {labels[status]}
    </span>
  )
}

function formatCurrency(value: string): string {
  const num = parseFloat(value)
  if (isNaN(num)) return '—'
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    maximumFractionDigits: 0,
  }).format(num)
}

function BudgetBar({ category }: { category: SupportCategory }) {
  const pct = Math.min(category.utilisation_percent, 100)
  const barColor =
    category.alert_level === 'overspent' || category.alert_level === 'critical'
      ? 'bg-red-500'
      : category.alert_level === 'warning'
        ? 'bg-yellow-500'
        : 'bg-blue-600'

  return (
    <div className="mb-4">
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="font-medium text-gray-800">
          {category.ndis_support_category}
        </span>
        <div className="flex items-center gap-2">
          {category.alert_level && (
            <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
              <AlertTriangle className="h-3 w-3" />
              {category.alert_level}
            </span>
          )}
          <span className="text-gray-500">
            {category.utilisation_percent.toFixed(1)}%
          </span>
        </div>
      </div>
      <div
        role="progressbar"
        aria-valuenow={Math.round(category.utilisation_percent)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${category.ndis_support_category} budget usage`}
        className="h-2 w-full overflow-hidden rounded-full bg-gray-200"
      >
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mt-1 flex justify-between text-xs text-gray-500">
        <span>Spent: {formatCurrency(category.budget_spent)}</span>
        <span>Allocated: {formatCurrency(category.budget_allocated)}</span>
      </div>
    </div>
  )
}

interface Props {
  participant: Participant
  plans: Plan[]
  auditLog: AuditLogEntry[]
}

export function ParticipantProfileClient({ participant, plans, auditLog }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('overview')

  const activePlan = plans.find((p) => p.status === 'active') ?? null

  const totalBudget = activePlan ? parseFloat(activePlan.total_budget) : 0
  const totalSpent = activePlan
    ? activePlan.support_categories.reduce(
        (sum, c) => sum + parseFloat(c.budget_spent),
        0
      )
    : 0
  const totalRemaining = totalBudget - totalSpent
  const overallPct = totalBudget > 0 ? (totalSpent / totalBudget) * 100 : 0

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'plans', label: 'Plans' },
    { id: 'audit', label: 'Audit Log' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        {/* Back link */}
        <div className="mb-6">
          <Link
            href="/dashboard/participants"
            className="text-sm text-blue-600 hover:underline"
          >
            ← Back to Participants
          </Link>
        </div>

        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">
                {participant.legal_name}
              </h1>
              {participant.preferred_name && (
                <span className="text-lg text-gray-500">
                  ({participant.preferred_name})
                </span>
              )}
              <StatusBadge status={participant.status} />
            </div>
            <p className="mt-1 font-mono text-sm text-gray-500">
              NDIS: {participant.ndis_number}
            </p>
          </div>
          <Link
            href={`/dashboard/participants/${participant.id}/edit`}
            className="rounded-md bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm ring-1 ring-gray-300 hover:bg-gray-50"
          >
            Edit
          </Link>
        </div>

        {/* Details grid */}
        <div className="mb-8 rounded-lg bg-white p-6 shadow">
          <dl className="grid grid-cols-2 gap-x-8 gap-y-4 sm:grid-cols-3 lg:grid-cols-5">
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">
                Date of Birth
              </dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(participant.date_of_birth).toLocaleDateString('en-AU')}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">
                Email
              </dt>
              <dd className="mt-1 text-sm text-gray-900">
                {participant.email ?? '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">
                Phone
              </dt>
              <dd className="mt-1 text-sm text-gray-900">
                {participant.phone ?? '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">
                Address
              </dt>
              <dd className="mt-1 text-sm text-gray-900">
                {participant.address ?? '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">
                Portal Access
              </dt>
              <dd className="mt-1">
                {participant.portal_access ? (
                  <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                    Yes
                  </span>
                ) : (
                  <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
                    No
                  </span>
                )}
              </dd>
            </div>
          </dl>
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`whitespace-nowrap border-b-2 py-3 text-sm font-medium ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Overview tab */}
        {activeTab === 'overview' && (
          <div>
            {activePlan ? (
              <>
                {/* Active plan summary */}
                <div className="mb-6 rounded-lg bg-white p-6 shadow">
                  <h2 className="mb-4 text-lg font-semibold text-gray-800">
                    Current Active Plan
                  </h2>
                  <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
                        Plan Start
                      </p>
                      <p className="mt-1 text-sm text-gray-900">
                        {new Date(activePlan.plan_start_date).toLocaleDateString('en-AU')}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
                        Plan End
                      </p>
                      <p className="mt-1 text-sm text-gray-900">
                        {new Date(activePlan.plan_end_date).toLocaleDateString('en-AU')}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
                        Total Budget
                      </p>
                      <p className="mt-1 text-sm font-medium text-gray-900">
                        {formatCurrency(activePlan.total_budget)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
                        Remaining
                      </p>
                      <p className="mt-1 text-sm font-medium text-gray-900">
                        {formatCurrency(String(totalRemaining))}
                      </p>
                    </div>
                  </div>

                  {/* Overall progress bar */}
                  <div className="mb-1 flex justify-between text-xs text-gray-500">
                    <span>Overall utilisation</span>
                    <span>{overallPct.toFixed(1)}%</span>
                  </div>
                  <div className="mb-6 h-2.5 w-full overflow-hidden rounded-full bg-gray-200">
                    <div
                      className={`h-full rounded-full ${
                        overallPct >= 100
                          ? 'bg-red-500'
                          : overallPct >= 85
                            ? 'bg-yellow-500'
                            : 'bg-blue-600'
                      }`}
                      style={{ width: `${Math.min(overallPct, 100)}%` }}
                    />
                  </div>

                  {/* Category bars */}
                  {activePlan.support_categories.length > 0 && (
                    <div>
                      <h3 className="mb-3 text-sm font-semibold text-gray-700">
                        Budget by Support Category
                      </h3>
                      {activePlan.support_categories.map((cat) => (
                        <BudgetBar key={cat.id} category={cat} />
                      ))}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="rounded-lg bg-white p-8 text-center shadow">
                <p className="text-sm text-gray-500">No active plan found.</p>
              </div>
            )}

            {/* Quick stats */}
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-white p-4 shadow">
                <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
                  Total Plans
                </p>
                <p className="mt-1 text-2xl font-bold text-gray-900">{plans.length}</p>
              </div>
              <div className="rounded-lg bg-white p-4 shadow">
                <Link
                  href={`/dashboard/invoices?participant_id=${participant.id}`}
                  className="block"
                >
                  <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
                    Linked Invoices
                  </p>
                  <p className="mt-1 text-sm font-medium text-blue-600 hover:underline">
                    View Invoices →
                  </p>
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Plans tab */}
        {activeTab === 'plans' && (
          <div className="overflow-hidden rounded-lg bg-white shadow">
            {plans.length === 0 ? (
              <div className="px-4 py-12 text-center text-sm text-gray-500">
                No plans found for this participant.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium text-gray-500">
                        Start Date
                      </th>
                      <th className="px-4 py-3 text-left font-medium text-gray-500">
                        End Date
                      </th>
                      <th className="px-4 py-3 text-right font-medium text-gray-500">
                        Total Budget
                      </th>
                      <th className="px-4 py-3 text-right font-medium text-gray-500">
                        Total Spent
                      </th>
                      <th className="px-4 py-3 text-right font-medium text-gray-500">
                        Utilisation
                      </th>
                      <th className="px-4 py-3 text-left font-medium text-gray-500">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {plans.map((plan) => {
                      const spent = plan.support_categories.reduce(
                        (sum, c) => sum + parseFloat(c.budget_spent),
                        0
                      )
                      const budget = parseFloat(plan.total_budget)
                      const pct = budget > 0 ? (spent / budget) * 100 : 0
                      return (
                        <tr key={plan.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-gray-700">
                            {new Date(plan.plan_start_date).toLocaleDateString('en-AU')}
                          </td>
                          <td className="px-4 py-3 text-gray-700">
                            {new Date(plan.plan_end_date).toLocaleDateString('en-AU')}
                          </td>
                          <td className="px-4 py-3 text-right font-medium text-gray-900">
                            {formatCurrency(plan.total_budget)}
                          </td>
                          <td className="px-4 py-3 text-right text-gray-700">
                            {formatCurrency(String(spent))}
                          </td>
                          <td className="px-4 py-3 text-right text-gray-700">
                            {pct.toFixed(1)}%
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                plan.status === 'active'
                                  ? 'bg-green-100 text-green-800'
                                  : plan.status === 'expired'
                                    ? 'bg-red-100 text-red-800'
                                    : 'bg-gray-100 text-gray-800'
                              }`}
                            >
                              {plan.status.charAt(0).toUpperCase() + plan.status.slice(1)}
                            </span>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Audit Log tab */}
        {activeTab === 'audit' && (
          <div className="overflow-hidden rounded-lg bg-white shadow">
            {auditLog.length === 0 ? (
              <div className="px-4 py-12 text-center text-sm text-gray-500">
                No audit log entries found.
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {[...auditLog]
                  .sort(
                    (a, b) =>
                      new Date(b.timestamp).getTime() -
                      new Date(a.timestamp).getTime()
                  )
                  .map((entry) => (
                    <li key={entry.id} className="px-6 py-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {entry.action}
                          </p>
                          <p className="text-xs text-gray-500">
                            by {entry.performed_by}
                          </p>
                          {entry.changes && (
                            <ul className="mt-2 space-y-1">
                              {Object.entries(entry.changes).map(([field, change]) => (
                                <li key={field} className="text-xs text-gray-500">
                                  <span className="font-medium">{field}:</span>{' '}
                                  <span className="text-red-600">
                                    {String(change.before ?? '—')}
                                  </span>{' '}
                                  →{' '}
                                  <span className="text-green-700">
                                    {String(change.after ?? '—')}
                                  </span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                        <time className="ml-4 shrink-0 text-xs text-gray-400">
                          {new Date(entry.timestamp).toLocaleString('en-AU')}
                        </time>
                      </div>
                    </li>
                  ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
