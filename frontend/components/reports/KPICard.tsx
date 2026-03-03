import type { ReactNode } from 'react'

interface KPICardProps {
  title: string
  value: string | number | null
  icon: string
  href?: string
  variant?: 'default' | 'warning' | 'danger' | 'success' | 'info'
}

const variantStyles: Record<string, string> = {
  default: 'border-gray-200 bg-white',
  warning: 'border-yellow-200 bg-yellow-50',
  danger: 'border-red-200 bg-red-50',
  success: 'border-green-200 bg-green-50',
  info: 'border-blue-200 bg-blue-50',
}

const titleStyles: Record<string, string> = {
  default: 'text-gray-600',
  warning: 'text-yellow-700',
  danger: 'text-red-700',
  success: 'text-green-700',
  info: 'text-blue-700',
}

const valueStyles: Record<string, string> = {
  default: 'text-gray-900',
  warning: 'text-yellow-900',
  danger: 'text-red-900',
  success: 'text-green-900',
  info: 'text-blue-900',
}

export function KPICard({ title, value, icon, href, variant = 'default' }: KPICardProps) {
  const content = (
    <div
      className={`flex items-center justify-between rounded-lg border p-5 shadow-sm transition hover:shadow-md ${variantStyles[variant]}`}
    >
      <div>
        <p className={`text-sm font-medium ${titleStyles[variant]}`}>{title}</p>
        <p className={`mt-1 text-3xl font-bold ${valueStyles[variant]}`}>
          {value ?? '—'}
        </p>
      </div>
      <span className="text-3xl">{icon}</span>
    </div>
  )

  if (href) {
    return (
      <a href={href} className="block">
        {content}
      </a>
    )
  }
  return content
}
