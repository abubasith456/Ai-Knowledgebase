// Vite defines import.meta.env at runtime; for type safety, cast to any
export const BACKEND_URL = (import.meta as any).env?.VITE_BACKEND_URL || 'http://localhost:8000'

