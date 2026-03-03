'use client'

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { InvoiceStatusSummary } from '@/lib/types/reports'

const STATUS_COLORS: Record<string, string> = {
  pending: '#f59e0b',
  approved: '#10b981',
  rejected: '#ef4444',
  flagged: '#f97316',
  info_requested: '#6366f1',
  other: '#9ca3af',
}

interface Props {
  data: InvoiceStatusSummary
}

export function InvoiceStatusDonut({ data }: Props) {
  const chartData = Object.entries(data)
    .filter(([, v]) => (v as number) > 0)
    .map(([key, value]) => ({
      name: key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      value: value as number,
      key,
    }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={70}
          outerRadius={110}
          paddingAngle={3}
          dataKey="value"
        >
          {chartData.map((entry) => (
            <Cell key={entry.key} fill={STATUS_COLORS[entry.key] ?? '#9ca3af'} />
          ))}
        </Pie>
        <Tooltip formatter={(v) => [v, 'Invoices']} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}
