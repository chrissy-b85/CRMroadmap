'use client'

import type { BudgetAlert } from '@/lib/types/budget'

interface BudgetAlertsPanelProps {
  alerts: BudgetAlert[]
}

const severityConfig: Record<
  BudgetAlert['severity'],
  { border: string; bg: string; badge: string; label: string; icon: string }
> = {
  critical: {
    border: 'border-red-300',
    bg: 'bg-red-50',
    badge: 'bg-red-100 text-red-800',
    label: 'Critical',
    icon: '🔴',
  },
  warning: {
    border: 'border-yellow-300',
    bg: 'bg-yellow-50',
    badge: 'bg-yellow-100 text-yellow-800',
    label: 'Warning',
    icon: '🟡',
  },
  info: {
    border: 'border-blue-200',
    bg: 'bg-blue-50',
    badge: 'bg-blue-100 text-blue-800',
    label: 'Info',
    icon: '🔵',
  },
}

const severityOrder: Record<BudgetAlert['severity'], number> = {
  critical: 0,
  warning: 1,
  info: 2,
}

export default function BudgetAlertsPanel({ alerts }: BudgetAlertsPanelProps) {
  const sorted = [...alerts].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  )

  if (sorted.length === 0) {
    return (
      <div className="rounded-lg border border-green-200 bg-green-50 p-5 text-sm text-green-700">
        ✅ No active budget alerts.
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {sorted.map((alert, idx) => {
        const cfg = severityConfig[alert.severity]
        const key = `${alert.alert_type}-${alert.category_id ?? 'plan'}-${idx}`
        return (
          <div
            key={key}
            className={`flex items-start gap-3 rounded-lg border ${cfg.border} ${cfg.bg} p-4`}
          >
            <span className="text-lg leading-none">{cfg.icon}</span>
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${cfg.badge}`}
                >
                  {cfg.label}
                </span>
                <span className="text-xs font-medium text-gray-600">{alert.alert_type}</span>
                {alert.category_name && (
                  <span className="text-xs text-gray-500">— {alert.category_name}</span>
                )}
              </div>
              <p className="mt-1 text-sm text-gray-800">{alert.message}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
