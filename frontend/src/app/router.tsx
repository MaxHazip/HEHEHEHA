import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import AppLayout from '@/layouts/AppLayout'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import TicketsPage from '@/pages/TicketsPage'
import ClientChatPage from '@/pages/ClientChatPage'

export default function AppRouter() {
  const role = useAuthStore((s) => s.role)

  // Если роль не выбрана — показываем экран входа
  if (!role) {
    return (
      <Routes>
        <Route path="*" element={<LoginPage />} />
      </Routes>
    )
  }

  // Если зашел Клиент — показываем только чат
  if (role === 'client') {
    return (
      <Routes>
        <Route path="*" element={<ClientChatPage />} />
      </Routes>
    )
  }

  // Если зашел Диспетчер — показываем полный интерфейс (AppLayout)
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/tickets" element={<TicketsPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  )
}