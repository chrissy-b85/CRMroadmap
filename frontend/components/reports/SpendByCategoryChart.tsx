'use client'

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { SpendByCategory } from '@/lib/types/reports'

const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1',
]

interface Props {
  data: SpendByCategory[]
}

export function SpendByCategoryChart({ data }: Props) {
  const chartData = data.map((d) => ({
    name: d.ndis_support_category,
    spend: parseFloat(d.total_spend),
  }))

  return (
    <ResponsiveContainer width="100%" height={Math.max(200, chartData.length * 45)}>
      <BarChart layout="vertical" data={chartData} margin={{ left: 20, right: 30 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis
          type="number"
          tickFormatter={(v) => `$${(v as number).toLocaleString()}`}
        />
        <YAxis type="category" dataKey="name" width={200} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v) => [`$${(v as number).toLocaleString()}`, 'Spend']} />
        <Bar dataKey="spend" radius={[0, 4, 4, 0]}>
          {chartData.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
