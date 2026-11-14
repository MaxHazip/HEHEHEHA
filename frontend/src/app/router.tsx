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
import EngineersPage from '@/pages/EngineersPage'
import KnowledgePage from '@/pages/KnowledgePage'

export default function AppRouter() {
  const role = useAuthStore((s) => s.role)

  if (!role) {
    return <Routes><Route path="*" element={<LoginPage />} /></Routes>
  }

  if (role === 'client') {
    return (
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/chat" replace />} />
          <Route path="/chat" element={<ClientChatPage />} />
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Route>
      </Routes>
    )
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
            <Route path="/employees" element={<EngineersPage />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
          </>
        )}

        {/* Маршрут инженера */}
        {role === 'engineer' && (
          <Route path="/my-tasks" element={<EngineerPage />} />
        )}

        {/* Маршрут админа */}
        {role === 'admin' && (
          <>
            <Route path="/analytics" element={<AdminDashboardPage />} />
            <Route path="/employees" element={<EngineersPage />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
          </>
        )}

        <Route path="*" element={<Navigate to={role === 'engineer' ? '/my-tasks' : role === 'admin' ? '/analytics' : '/dashboard'} replace />} />
      </Route>
    </Routes>
  )
}