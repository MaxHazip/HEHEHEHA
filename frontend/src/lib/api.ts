import axios from 'axios'

// В dev запросы идут на /api и проксируются Vite на backend (см. vite.config.ts).
// В production задайте VITE_API_URL или раздавайте frontend с того же origin.
const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined) ?? ''

export const api = axios.create({
  baseURL: API_URL,
  // Обычные запросы: 5 минут (загрузка аудио/файлов тоже сюда).
  // Долгие ИИ-запросы переопределяют таймаут на 10 минут
  // (см. chatApi.ts / callsApi.ts).
  timeout: 300_000,
})

export function apiUrl(path: string | null | undefined): string | undefined {
  if (!path) return undefined
  if (/^https?:\/\//.test(path)) return path
  const base = API_URL.replace(/\/$/, '')
  return `${base}${path.startsWith('/') ? path : `/${path}`}`
}

export function wsUrl(path: string): string {
  const base = API_URL.replace(/\/$/, '')
  if (base) {
    return `${base.replace(/^http/, 'ws')}${path.startsWith('/') ? path : `/${path}`}`
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}${path.startsWith('/') ? path : `/${path}`}`
}
