import axios from 'axios'
import { API_KEY, BACKEND_URL } from './config'

export const http = axios.create({ baseURL: BACKEND_URL })

http.interceptors.request.use(cfg => {
  const key = API_KEY || localStorage.getItem('kb_api_key') || ''
  if (key) {
    cfg.headers = cfg.headers || {}
    // backend expects 'x-api-key'
    ;(cfg.headers as any)['x-api-key'] = key
  }
  return cfg
})

