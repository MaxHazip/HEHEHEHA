import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/Sidebar'
import Topbar from '@/components/Topbar'
import { useAuthStore } from '@/store/authStore'

export default function AppLayout() {
  const role = useAuthStore((s) => s.role)
  const showSidebar = role !== 'engineer' && role !== 'admin'

  return (
    <div className="app-background">
      <div className="app-shell">
        {showSidebar && <Sidebar />}

        <div className="app-main">
          <Topbar />

          <main className="app-content">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}