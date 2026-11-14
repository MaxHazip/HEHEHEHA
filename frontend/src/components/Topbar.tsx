import { useAuthStore } from '@/store/authStore'
import { LogOut } from 'lucide-react'

export default function Topbar() {
  const logout = useAuthStore((s) => s.logout)

  return (
    <header className="h-14 shrink-0 bg-white border-b border-slate-200 flex items-center px-6 justify-between">
      <div className="text-sm text-slate-500">Рабочее место диспетчера</div>
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium text-slate-700">Иван Диспетчеров</span>
        <button onClick={logout} className="text-slate-400 hover:text-rose-500 transition" title="Выйти">
          <LogOut size={18} />
        </button>
      </div>
    </header>
  )
}