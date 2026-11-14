import axios from 'axios'

export const api = axios.create({
  // Берем URL из файла .env, если его нет — используем localhost:8000/api
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
})

// Перехватчик: автоматически добавляет токен авторизации к каждому запросу
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})