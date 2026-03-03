interface OCRConfidenceBarProps {
  confidence: number | null
}

function getConfidenceConfig(confidence: number): {
  color: string
  bg: string
  label: string
} {
  if (confidence >= 0.9) {
    return { color: 'bg-green-500', bg: 'bg-green-100', label: 'High' }
  }
  if (confidence >= 0.75) {
    return { color: 'bg-yellow-500', bg: 'bg-yellow-100', label: 'Medium' }
  }
  return { color: 'bg-red-500', bg: 'bg-red-100', label: 'Low' }
}

export default function OCRConfidenceBar({ confidence }: OCRConfidenceBarProps) {
  if (confidence == null) {
    return <span className="text-xs text-gray-400">N/A</span>
  }

  const pct = Math.round(confidence * 100)
  const { color, bg, label } = getConfidenceConfig(confidence)

  return (
    <div className="flex items-center gap-2 min-w-[120px]">
      <div className={`relative h-2 flex-1 rounded-full ${bg}`}>
        <div
          className={`absolute left-0 top-0 h-2 rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-medium tabular-nums w-9 text-right">
        {pct}%
      </span>
      <span className="sr-only">{label} confidence</span>
    </div>
  )
}
