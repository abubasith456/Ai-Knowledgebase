import React from 'react'

export function ProgressBar({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, Math.round(value)))
  return (
    <div className="w-full h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
      <div className="h-full bg-indigo-600 transition-all" style={{ width: `${pct}%` }} />
    </div>
  )
}

