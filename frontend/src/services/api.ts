import axios from 'axios'

// В dev VITE_API_URL обычно не задан — используем относительный /api,
// который проксирует Vite. В production можно задать полный URL.
const rawBase = (import.meta.env.VITE_API_URL as string | undefined) ?? ''
const base = rawBase.replace(/\/$/, '')
const baseURL = base.endsWith('/api') ? base : `${base}/api`

export const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  // ИИ на CPU может отвечать минутами.
  timeout: 300_000,
})

// Автоматически добавляет токен, если он есть (сейчас логин — mock).
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
