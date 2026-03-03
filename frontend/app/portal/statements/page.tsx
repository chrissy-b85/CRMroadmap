"use client";

import { useEffect, useState } from "react";
import type { Statement } from "@/lib/types/statement";
import { getMyStatements } from "@/lib/api/statements";

function formatCurrency(amount: string): string {
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
  }).format(parseFloat(amount));
}

function SkeletonRow() {
  return (
    <tr className="animate-pulse">
      {Array.from({ length: 4 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 rounded bg-gray-200" />
        </td>
      ))}
    </tr>
  );
}

export default function PortalStatementsPage() {
  const [statements, setStatements] = useState<Statement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMyStatements()
      .then(setStatements)
      .catch((err) =>
        setError(
          err instanceof Error ? err.message : "Failed to load statements",
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-gray-900">My Statements</h1>
        <p className="mt-1 text-sm text-gray-500">
          Download your monthly NDIS plan statements.
        </p>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-500">
                Period
              </th>
              <th className="px-4 py-3 text-right font-medium text-gray-500">
                Invoices
              </th>
              <th className="px-4 py-3 text-right font-medium text-gray-500">
                Total Amount
              </th>
              <th className="px-4 py-3 text-left font-medium text-gray-500">
                Download
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading
              ? Array.from({ length: 3 }).map((_, i) => <SkeletonRow key={i} />)
              : statements.map((stmt) => (
                  <tr key={stmt.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {stmt.statement_period}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-700">
                      {stmt.invoice_count}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900">
                      {formatCurrency(stmt.total_amount)}
                    </td>
                    <td className="px-4 py-3">
                      <a
                        href={stmt.download_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
                      >
                        📄 Download PDF
                      </a>
                    </td>
                  </tr>
                ))}

            {!loading && statements.length === 0 && !error && (
              <tr>
                <td
                  colSpan={4}
                  className="px-4 py-12 text-center text-sm text-gray-500"
                >
                  No statements available yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
