import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import AppLayout from '@/layouts/AppLayout'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import TicketsPage from '@/pages/TicketsPage'
import ClientChatPage from '@/pages/ClientChatPage'
import EngineerPage from '@/pages/EngineerPage'
import AdminDashboardPage from '@/pages/AdminDashboardPage'
import DispatcherCallsPage from '@/pages/DispatcherCallsPage'

export default function AppRouter() {
  const role = useAuthStore((s) => s.role)

  const queryClient = useQueryClient()
  useEffect(() => {
    if (!role) queryClient.clear()
    const interceptor = api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401 && !error.config?.url?.startsWith('/api/users/')) {
          useAuthStore.setState({ role: null, user: null })
        }
        return Promise.reject(error)
      },
    )
    if (role) {
      void api.get('/api/users/me').catch((error) => {
        if (error.response?.status === 401) useAuthStore.setState({ role: null, user: null })
      })
    }
    return () => api.interceptors.response.eject(interceptor)
  }, [queryClient, role])

  if (!role) {
    return <Routes><Route path="*" element={<LoginPage />} /></Routes>
  }

  if (role === 'client') {
    return <Routes><Route path="*" element={<ClientChatPage />} /></Routes>
  }

  // Общий Layout для Диспетчера, Инженера и Админа
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to={role === 'engineer' ? '/my-tasks' : role === 'admin' ? '/analytics' : '/dashboard'} replace />} />
        
        {/* Маршруты диспетчера */}
        {role === 'dispatcher' && (
          <>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/tickets" element={<TicketsPage />} />
            <Route path="/calls" element={<DispatcherCallsPage />} />
          </>
        )}

        {/* Маршрут инженера */}
        {role === 'engineer' && (
          <Route path="/my-tasks" element={<EngineerPage />} />
        )}

        {/* Маршрут админа */}
        {role === 'admin' && (
          <Route path="/analytics" element={<AdminDashboardPage />} />
        )}

        <Route path="*" element={<Navigate to={role === 'engineer' ? '/my-tasks' : role === 'admin' ? '/analytics' : '/dashboard'} replace />} />
      </Route>
    </Routes>
  )
}