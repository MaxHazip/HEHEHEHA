import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import AppLayout from '@/layouts/AppLayout'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import TicketsPage from '@/pages/TicketsPage'
import ClientChatPage from '@/pages/ClientChatPage'
import EngineerPage from '@/pages/EngineerPage'
import AdminDashboardPage from '@/pages/AdminDashboardPage'
// Добавили импорты новых страниц
import EngineersPage from '@/pages/EngineersPage'
import DispatcherCallsPage from '@/pages/DispatcherCallsPage'

export default function AppRouter() {
  const role = useAuthStore((s) => s.role)

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
            {/* Добавили маршруты для Звонков и Исполнителей */}
            <Route path="/calls" element={<DispatcherCallsPage />} />
            <Route path="/employees" element={<EngineersPage />} />
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