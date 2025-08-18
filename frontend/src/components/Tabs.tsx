import React from 'react'
import clsx from 'clsx'

interface TabsProps {
  value: string
  onValueChange: (value: string) => void
  children: React.ReactNode
}

interface TabsListProps {
  children: React.ReactNode
}

interface TabsTriggerProps {
  value: string
  children: React.ReactNode
}

interface TabsContentProps {
  value: string
  children: React.ReactNode
}

const TabsContext = React.createContext<{
  value: string
  onValueChange: (value: string) => void
}>({ value: '', onValueChange: () => {} })

export function Tabs({ value, onValueChange, children }: TabsProps) {
  return (
    <TabsContext.Provider value={{ value, onValueChange }}>
      <div>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({ children }: TabsListProps) {
  return (
    <div className="inline-flex h-10 items-center justify-center rounded-md bg-gray-100 dark:bg-gray-800 p-1">
      {children}
    </div>
  )
}

export function TabsTrigger({ value, children }: TabsTriggerProps) {
  const { value: currentValue, onValueChange } = React.useContext(TabsContext)
  const isActive = currentValue === value

  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
        isActive
          ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 shadow-sm'
          : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
      )}
      onClick={() => onValueChange(value)}
    >
      {children}
    </button>
  )
}

export function TabsContent({ value, children }: TabsContentProps) {
  const { value: currentValue } = React.useContext(TabsContext)
  
  if (currentValue !== value) return null
  
  return (
    <div className="mt-6 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
      {children}
    </div>
  )
}