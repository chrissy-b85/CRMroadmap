"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import type { Statement } from "@/lib/types/statement";
import {
  emailStatement,
  generateStatement,
  getParticipantStatements,
} from "@/lib/api/statements";

type Tab = "statements";

function formatCurrency(amount: string): string {
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
  }).format(parseFloat(amount));
}

function SkeletonRow() {
  return (
    <tr className="animate-pulse">
      {Array.from({ length: 6 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 rounded bg-gray-200" />
        </td>
      ))}
    </tr>
  );
}

export default function ParticipantDetailPage() {
  const params = useParams<{ id: string }>();
  const participantId = params?.id ?? "";

  const [activeTab] = useState<Tab>("statements");
  const [statements, setStatements] = useState<Statement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchStatements = useCallback(async () => {
    if (!participantId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getParticipantStatements(participantId);
      setStatements(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load statements",
      );
    } finally {
      setLoading(false);
    }
  }, [participantId]);

  useEffect(() => {
    void fetchStatements();
  }, [fetchStatements]);

  async function handleGenerate() {
    const now = new Date();
    // Default to the previous month (statements cover completed months)
    const prevMonth = now.getMonth() === 0 ? 12 : now.getMonth();
    const year =
      now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear();
    const month = prevMonth;
    setActionLoading("generate");
    try {
      await generateStatement(participantId, year, month);
      await fetchStatements();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleEmail(stmt: Statement) {
    setActionLoading(stmt.id);
    try {
      await emailStatement(participantId, stmt.year, stmt.month);
      await fetchStatements();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Email failed");
    } finally {
      setActionLoading(null);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Back link */}
        <div className="mb-6">
          <a
            href="/dashboard"
            className="text-sm text-blue-600 hover:underline"
          >
            ← Back to Dashboard
          </a>
        </div>

        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">
            Participant Detail
          </h1>
        </div>

        {/* Tab bar — currently only Statements tab is implemented */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-6">
            <span className="border-b-2 border-blue-600 py-3 text-sm font-medium text-blue-600">
              Statements
            </span>
          </nav>
        </div>

        {/* Error state */}
        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="mb-4 flex justify-end">
          <button
            type="button"
            onClick={() => void handleGenerate()}
            disabled={actionLoading === "generate"}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {actionLoading === "generate"
              ? "Generating…"
              : "+ Generate Statement"}
          </button>
        </div>

        {/* Statements table */}
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
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
                    Generated
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">
                    Emailed
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {loading
                  ? Array.from({ length: 3 }).map((_, i) => (
                      <SkeletonRow key={i} />
                    ))
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
                        <td className="px-4 py-3 text-gray-500">
                          {new Date(stmt.generated_at).toLocaleDateString(
                            "en-AU",
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-500">
                          {stmt.emailed_at
                            ? new Date(stmt.emailed_at).toLocaleDateString(
                                "en-AU",
                              )
                            : "—"}
                        </td>
                        <td className="flex items-center gap-2 px-4 py-3">
                          <a
                            href={stmt.download_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="rounded-md bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-200"
                          >
                            Download
                          </a>
                          <button
                            type="button"
                            onClick={() => void handleEmail(stmt)}
                            disabled={actionLoading === stmt.id}
                            className="rounded-md bg-blue-100 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-200 disabled:opacity-50"
                          >
                            {actionLoading === stmt.id ? "Sending…" : "Email"}
                          </button>
                        </td>
                      </tr>
                    ))}

                {!loading && statements.length === 0 && !error && (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-4 py-12 text-center text-sm text-gray-500"
                    >
                      No statements generated yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
