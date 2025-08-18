export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
export const API_KEY = import.meta.env.VITE_API_KEY || localStorage.getItem('kb_api_key') || ''

