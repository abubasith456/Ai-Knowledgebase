import React, { useState, useEffect } from 'react'
import V1Manager from './components/V1Manager'
import { ThemeToggle } from './components/ThemeToggle'

export default function App() {
	const [isDark, setIsDark] = useState(() => {
		if (typeof window !== 'undefined') {
			return localStorage.getItem('theme') === 'dark' || 
					(!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
		}
		return false
	})

	useEffect(() => {
		if (isDark) {
			document.documentElement.classList.add('dark')
			localStorage.setItem('theme', 'dark')
		} else {
			document.documentElement.classList.remove('dark')
			localStorage.setItem('theme', 'light')
		}
	}, [isDark])

	return (
		<div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
			<div className="max-w-7xl mx-auto p-6 space-y-8">
				<header className="flex items-center justify-between">
					<div>
						<h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
							Doc KB
						</h1>
						<p className="text-gray-600 dark:text-gray-400">Versioned API Manager (v1)</p>
					</div>
					<ThemeToggle isDark={isDark} onToggle={() => setIsDark(!isDark)} />
				</header>

				<V1Manager />
			</div>
		</div>
	)
}