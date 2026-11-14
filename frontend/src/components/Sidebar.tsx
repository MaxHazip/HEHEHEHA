import { NavLink } from 'react-router-dom'
import { BookOpen, Inbox, LayoutDashboard, Wrench, Ticket, Users } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

export default function Sidebar() {
  const role = useAuthStore((s) => s.role)

  // Меню для диспетчера
  const dispatcherMenu = [
    { to: '/dashboard', label: 'Главная', icon: LayoutDashboard },
    { to: '/tickets', label: 'Входящие заявки', icon: Inbox },
    { to: '/employees', label: 'Исполнители', icon: Users },
    { to: '/knowledge', label: 'База знаний', icon: BookOpen },
  ]

  // Меню для инженера (заменили Tool на Wrench)
  const engineerMenu = [
    { to: '/my-tasks', label: 'Мои задачи', icon: Wrench },
  ]

  const menu = role === 'engineer' ? engineerMenu : dispatcherMenu

  return (
    <aside className="w-64 shrink-0 bg-slate-900 text-slate-300 flex flex-col">
      <div className="px-5 py-6 text-xl font-semibold text-white">
        Dispatch<span className="text-blue-400">AI</span>
      </div>
      <nav className="flex-1 px-3 space-y-1">
        {menu.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                isActive ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 text-xs text-slate-500">v0.3.0 · mock</div>
    </aside>
  )
}