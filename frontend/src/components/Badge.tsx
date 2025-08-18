import React from 'react'
import clsx from 'clsx'

type Props = {
  color?: 'gray' | 'green' | 'red' | 'blue' | 'yellow'
  children: React.ReactNode
}

export function Badge({ color = 'gray', children }: Props) {
  const colors: Record<string, string> = {
    gray: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
    green: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    red: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
    blue: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    yellow: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  }
  return <span className={clsx('inline-flex items-center rounded-full px-2 py-0.5 text-xs', colors[color])}>{children}</span>
}

