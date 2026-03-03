'use client'

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { SpendOverTime } from '@/lib/types/reports'

interface Props {
  data: SpendOverTime[]
}

export function SpendOverTimeChart({ data }: Props) {
  const chartData = data.map((d) => ({
    period: d.period,
    spend: parseFloat(d.total_spend),
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={chartData} margin={{ left: 10, right: 10 }}>
        <defs>
          <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="period" tick={{ fontSize: 12 }} />
        <YAxis tickFormatter={(v) => `$${(v as number).toLocaleString()}`} />
        <Tooltip formatter={(v) => [`$${(v as number).toLocaleString()}`, 'Spend']} />
        <Area
          type="monotone"
          dataKey="spend"
          stroke="#3b82f6"
          fill="url(#spendGradient)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
