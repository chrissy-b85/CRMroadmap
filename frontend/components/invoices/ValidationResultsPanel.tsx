'use client'

import { useState } from 'react'
import { CheckCircle, XCircle, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import type { ValidationResult } from '@/lib/types/invoice'

interface ValidationResultsPanelProps {
  results: ValidationResult[]
}

export default function ValidationResultsPanel({ results }: ValidationResultsPanelProps) {
  const [showPassed, setShowPassed] = useState(false)

  const failed = results.filter((r) => !r.passed && r.severity === 'error')
  const warnings = results.filter((r) => !r.passed && r.severity === 'warning')
  const passed = results.filter((r) => r.passed)

  return (
    <div className="space-y-3">
      {failed.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-red-700">
            Failed Rules ({failed.length})
          </h4>
          {failed.map((r, i) => (
            <div
              key={i}
              className="flex items-start gap-2 rounded-md bg-red-50 px-3 py-2 text-sm"
            >
              <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
              <div>
                <span className="font-medium text-red-800">{r.rule_name}</span>
                <p className="text-red-700">{r.message}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {warnings.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-yellow-700">
            Warnings ({warnings.length})
          </h4>
          {warnings.map((r, i) => (
            <div
              key={i}
              className="flex items-start gap-2 rounded-md bg-yellow-50 px-3 py-2 text-sm"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-yellow-600" />
              <div>
                <span className="font-medium text-yellow-800">{r.rule_name}</span>
                <p className="text-yellow-700">{r.message}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {passed.length > 0 && (
        <div>
          <button
            type="button"
            onClick={() => setShowPassed((p) => !p)}
            className="flex items-center gap-1 text-sm font-medium text-gray-500 hover:text-gray-700"
          >
            {showPassed ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
            Passed Rules ({passed.length})
          </button>

          {showPassed && (
            <div className="mt-2 space-y-1">
              {passed.map((r, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 rounded-md bg-green-50 px-3 py-2 text-sm"
                >
                  <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-green-600" />
                  <div>
                    <span className="font-medium text-green-800">{r.rule_name}</span>
                    <p className="text-green-700">{r.message}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {results.length === 0 && (
        <p className="text-sm text-gray-500">No validation results available.</p>
      )}
    </div>
  )
}
