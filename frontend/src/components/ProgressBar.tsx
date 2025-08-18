import React from 'react'

interface ProgressBarProps {
  value: number
  label?: string
  showPercentage?: boolean
  variant?: 'default' | 'success' | 'error'
}

export function ProgressBar({ value, label, showPercentage = true, variant = 'default' }: ProgressBarProps) {
  const pct = Math.max(0, Math.min(100, Math.round(value)))
  
  const colorClasses = {
    default: 'bg-indigo-600',
    success: 'bg-green-600',
    error: 'bg-red-600'
  }

  return (
    <div className="w-full space-y-2">
      {(label || showPercentage) && (
        <div className="flex justify-between items-center text-sm">
          {label && <span className="text-gray-700 dark:text-gray-300">{label}</span>}
          {showPercentage && <span className="text-gray-500 dark:text-gray-400">{pct}%</span>}
        </div>
      )}
      <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full transition-all duration-300 ease-in-out ${colorClasses[variant]}`} 
          style={{ width: `${pct}%` }} 
        />
      </div>
    </div>
  )
}

