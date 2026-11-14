import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/Sidebar'
import Topbar from '@/components/Topbar'
import { useAuthStore } from '@/store/authStore'

export default function AppLayout() {
  const role = useAuthStore((s) => s.role)
  const showSidebar = role !== 'engineer'

  return (
    <div className="h-screen flex overflow-hidden">
      {showSidebar && <Sidebar />}
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar />
        <main className="flex-1 overflow-auto p-6 bg-slate-50">
          <Outlet />
        </main>
      </div>
    </div>
  )
}