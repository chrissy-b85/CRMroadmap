'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import {
  getSpendByCategory,
  getSpendOverTime,
  getProviderAnalytics,
  getFlaggedInvoicesSummary,
} from '@/lib/api/reports'
import type {
  SpendByCategory,
  SpendOverTime,
  ProviderAnalytics,
  FlaggedInvoiceSummary,
} from '@/lib/types/reports'
import { SpendByCategoryChart } from '@/components/reports/SpendByCategoryChart'
import { SpendOverTimeChart } from '@/components/reports/SpendOverTimeChart'
import { DateRangePicker } from '@/components/reports/DateRangePicker'
import { downloadCsv } from '@/lib/utils/exportCsv'

// Default date range: last 12 months
function defaultDates() {
  const to = new Date()
  const from = new Date(to)
  from.setFullYear(from.getFullYear() - 1)
  return {
    from: from.toISOString().slice(0, 10),
    to: to.toISOString().slice(0, 10),
  }
}

const TABS = ['Spend by Category', 'Spend Over Time', 'Provider Analytics', 'Flagged Invoices'] as const
type Tab = (typeof TABS)[number]

export default function ReportsPage() {
  const defaults = defaultDates()
  const [activeTab, setActiveTab] = useState<Tab>('Spend by Category')

  // Shared date range
  const [dateFrom, setDateFrom] = useState(defaults.from)
  const [dateTo, setDateTo] = useState(defaults.to)

  // Tab 1: Spend by Category
  const [categoryData, setCategoryData] = useState<SpendByCategory[]>([])
  const [categoryLoading, setCategoryLoading] = useState(false)

  // Tab 2: Spend Over Time
  const [timeData, setTimeData] = useState<SpendOverTime[]>([])
  const [granularity, setGranularity] = useState<'month' | 'week'>('month')
  const [timeLoading, setTimeLoading] = useState(false)

  // Tab 3: Provider Analytics
  const [providerData, setProviderData] = useState<ProviderAnalytics[]>([])
  const [providerLoading, setProviderLoading] = useState(false)
  const [sortField, setSortField] = useState<keyof ProviderAnalytics>('total_spend')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  // Tab 4: Flagged Invoices
  const [flaggedData, setFlaggedData] = useState<FlaggedInvoiceSummary[]>([])
  const [flaggedLoading, setFlaggedLoading] = useState(false)

  const loadCategoryData = useCallback(async () => {
    setCategoryLoading(true)
    try {
      const data = await getSpendByCategory({ dateFrom, dateTo })
      setCategoryData(data)
    } catch { /* ignore */ }
    setCategoryLoading(false)
  }, [dateFrom, dateTo])

  const loadTimeData = useCallback(async () => {
    setTimeLoading(true)
    try {
      const data = await getSpendOverTime({ granularity, dateFrom, dateTo })
      setTimeData(data)
    } catch { /* ignore */ }
    setTimeLoading(false)
  }, [dateFrom, dateTo, granularity])

  const loadProviderData = useCallback(async () => {
    setProviderLoading(true)
    try {
      const data = await getProviderAnalytics({ dateFrom, dateTo })
      setProviderData(data)
    } catch { /* ignore */ }
    setProviderLoading(false)
  }, [dateFrom, dateTo])

  const loadFlaggedData = useCallback(async () => {
    setFlaggedLoading(true)
    try {
      const data = await getFlaggedInvoicesSummary()
      setFlaggedData(data)
    } catch { /* ignore */ }
    setFlaggedLoading(false)
  }, [])

  useEffect(() => {
    if (activeTab === 'Spend by Category') loadCategoryData()
    if (activeTab === 'Spend Over Time') loadTimeData()
    if (activeTab === 'Provider Analytics') loadProviderData()
    if (activeTab === 'Flagged Invoices') loadFlaggedData()
  }, [activeTab, loadCategoryData, loadTimeData, loadProviderData, loadFlaggedData])

  const sortedProviders = [...providerData].sort((a, b) => {
    const av = a[sortField]
    const bv = b[sortField]
    const av2 = typeof av === 'string' ? parseFloat(av) : (av ?? 0)
    const bv2 = typeof bv === 'string' ? parseFloat(bv) : (bv ?? 0)
    if (typeof av2 === 'number' && typeof bv2 === 'number') {
      return sortDir === 'asc' ? av2 - bv2 : bv2 - av2
    }
    return sortDir === 'asc'
      ? String(av).localeCompare(String(bv))
      : String(bv).localeCompare(String(av))
  })

  function toggleSort(field: keyof ProviderAnalytics) {
    if (sortField === field) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortField(field); setSortDir('desc') }
  }

  function SortIcon({ field }: { field: keyof ProviderAnalytics }) {
    if (sortField !== field) return <span className="ml-1 text-gray-300">↕</span>
    return <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <Link href="/dashboard" className="text-sm text-blue-600 hover:underline">
            ← Dashboard
          </Link>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-6">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`whitespace-nowrap border-b-2 py-3 text-sm font-medium transition ${
                  activeTab === tab
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab 1: Spend by Category */}
        {activeTab === 'Spend by Category' && (
          <div>
            <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
              <DateRangePicker
                dateFrom={dateFrom}
                dateTo={dateTo}
                onDateFromChange={setDateFrom}
                onDateToChange={setDateTo}
              />
              <div className="flex gap-2">
                <button
                  onClick={loadCategoryData}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Apply
                </button>
                <button
                  onClick={() =>
                    downloadCsv(
                      `/api/v1/reports/export/invoices?date_from=${dateFrom}&date_to=${dateTo}`,
                      'invoices.csv'
                    )
                  }
                  className="rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
                >
                  Export CSV
                </button>
              </div>
            </div>
            {categoryLoading ? (
              <p className="py-10 text-center text-gray-500">Loading…</p>
            ) : categoryData.length === 0 ? (
              <p className="py-10 text-center text-gray-400">No data for the selected range</p>
            ) : (
              <>
                <div className="mb-8 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                  <SpendByCategoryChart data={categoryData} />
                </div>
                <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left font-semibold text-gray-600">Category</th>
                        <th className="px-6 py-3 text-right font-semibold text-gray-600">Total Spend</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {categoryData.map((row) => (
                        <tr key={row.ndis_support_category} className="hover:bg-gray-50">
                          <td className="px-6 py-3 text-gray-800">{row.ndis_support_category}</td>
                          <td className="px-6 py-3 text-right font-mono text-gray-800">
                            ${parseFloat(row.total_spend).toLocaleString('en-AU', { minimumFractionDigits: 2 })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        )}

        {/* Tab 2: Spend Over Time */}
        {activeTab === 'Spend Over Time' && (
          <div>
            <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-4">
                <DateRangePicker
                  dateFrom={dateFrom}
                  dateTo={dateTo}
                  onDateFromChange={setDateFrom}
                  onDateToChange={setDateTo}
                />
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700">Granularity</label>
                  <select
                    value={granularity}
                    onChange={(e) => setGranularity(e.target.value as 'month' | 'week')}
                    className="rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-blue-500 focus:outline-none"
                  >
                    <option value="month">Monthly</option>
                    <option value="week">Weekly</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={loadTimeData}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Apply
                </button>
                <button
                  onClick={() =>
                    downloadCsv(
                      `/api/v1/reports/export/invoices?date_from=${dateFrom}&date_to=${dateTo}&status=APPROVED`,
                      'spend-over-time.csv'
                    )
                  }
                  className="rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
                >
                  Export CSV
                </button>
              </div>
            </div>
            {timeLoading ? (
              <p className="py-10 text-center text-gray-500">Loading…</p>
            ) : timeData.length === 0 ? (
              <p className="py-10 text-center text-gray-400">No data for the selected range</p>
            ) : (
              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <SpendOverTimeChart data={timeData} />
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Provider Analytics */}
        {activeTab === 'Provider Analytics' && (
          <div>
            <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
              <DateRangePicker
                dateFrom={dateFrom}
                dateTo={dateTo}
                onDateFromChange={setDateFrom}
                onDateToChange={setDateTo}
              />
              <div className="flex gap-2">
                <button
                  onClick={loadProviderData}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Apply
                </button>
                <button
                  onClick={() =>
                    downloadCsv(
                      `/api/v1/reports/export/invoices?date_from=${dateFrom}&date_to=${dateTo}`,
                      'provider-invoices.csv'
                    )
                  }
                  className="rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
                >
                  Export CSV
                </button>
              </div>
            </div>
            {providerLoading ? (
              <p className="py-10 text-center text-gray-500">Loading…</p>
            ) : sortedProviders.length === 0 ? (
              <p className="py-10 text-center text-gray-400">No data for the selected range</p>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left font-semibold text-gray-600">Provider</th>
                      {(
                        [
                          ['invoice_count', 'Invoice Count'],
                          ['total_spend', 'Total Spend'],
                          ['avg_processing_days', 'Avg Processing Days'],
                          ['rejection_rate', 'Rejection Rate %'],
                        ] as [keyof ProviderAnalytics, string][]
                      ).map(([field, label]) => (
                        <th
                          key={field}
                          className="cursor-pointer px-6 py-3 text-right font-semibold text-gray-600 hover:text-gray-900"
                          onClick={() => toggleSort(field)}
                        >
                          {label}
                          <SortIcon field={field} />
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {sortedProviders.map((row) => (
                      <tr key={row.provider_id} className="hover:bg-gray-50">
                        <td className="px-6 py-3 font-medium text-gray-800">{row.business_name}</td>
                        <td className="px-6 py-3 text-right text-gray-700">{row.invoice_count}</td>
                        <td className="px-6 py-3 text-right font-mono text-gray-700">
                          ${parseFloat(row.total_spend).toLocaleString('en-AU', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-3 text-right text-gray-700">
                          {row.avg_processing_days != null ? row.avg_processing_days.toFixed(1) : '—'}
                        </td>
                        <td
                          className={`px-6 py-3 text-right font-medium ${
                            row.rejection_rate > 20
                              ? 'text-red-600'
                              : row.rejection_rate > 10
                              ? 'text-yellow-600'
                              : 'text-gray-700'
                          }`}
                        >
                          {row.rejection_rate.toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Flagged Invoices */}
        {activeTab === 'Flagged Invoices' && (
          <div>
            <div className="mb-6 flex justify-between">
              <p className="text-sm text-gray-600">Currently flagged invoices requiring attention</p>
              <button
                onClick={loadFlaggedData}
                className="rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
              >
                Refresh
              </button>
            </div>
            {flaggedLoading ? (
              <p className="py-10 text-center text-gray-500">Loading…</p>
            ) : flaggedData.length === 0 ? (
              <div className="rounded-lg border border-green-200 bg-green-50 p-8 text-center">
                <p className="text-lg font-medium text-green-700">✅ No flagged invoices</p>
                <p className="mt-1 text-sm text-green-600">All invoices are within policy</p>
              </div>
            ) : (
              <div className="space-y-4">
                {flaggedData.map((inv) => (
                  <div
                    key={inv.invoice_id}
                    className="rounded-lg border border-red-200 bg-white p-5 shadow-sm"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-gray-900">
                          Invoice #{inv.invoice_number ?? inv.invoice_id.slice(0, 8)}
                        </p>
                        <p className="mt-0.5 text-sm text-gray-500">
                          Date: {inv.invoice_date} · Amount: $
                          {parseFloat(inv.total_amount).toLocaleString('en-AU', {
                            minimumFractionDigits: 2,
                          })}
                        </p>
                        {inv.failing_rules.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {inv.failing_rules.map((rule) => (
                              <span
                                key={rule}
                                className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700"
                              >
                                {rule}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <Link
                        href={`/dashboard/invoices/${inv.invoice_id}`}
                        className="ml-4 shrink-0 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
                      >
                        Review
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  )
}
