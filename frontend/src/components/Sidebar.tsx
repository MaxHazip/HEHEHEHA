import { NavLink } from 'react-router-dom'
import {
  Inbox,
  LayoutDashboard,
  Wrench,
  Users,
  Phone,
  Settings,
  MessageSquare,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

export default function Sidebar() {
  const role = useAuthStore((s) => s.role)

  // Меню для диспетчера (ровно 4 вкладки, без Базы знаний)
  const dispatcherMenu = [
    {
      to: '/dashboard',
      label: 'Обзор',
      icon: LayoutDashboard,
    },
    {
      to: '/tickets',
      label: 'Заявки',
      icon: Inbox,
    },
    {
      to: '/employees',
      label: 'Исполнители',
      icon: Users,
    },
    {
      to: '/calls',
      label: 'Звонки',
      icon: Phone,
    },
  ]

  const engineerMenu = [
    {
      to: '/my-tasks',
      label: 'Мои задачи',
      icon: Wrench,
    },
  ]

  const clientMenu = [
    {
      to: '/chat',
      label: 'Поддержка',
      icon: MessageSquare,
    },
  ]

  const menu =
    role === 'engineer'
      ? engineerMenu
      : role === 'client'
        ? clientMenu
        : dispatcherMenu

  return (
    <aside className="app-sidebar">
      <div className="app-logo">
        <div className="app-logo-mark">D</div>
        <span className="app-logo-text">
          Dispatch<span style={{ fontWeight: 400 }}>AI</span>
        </span>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-section-title">
          Рабочее пространство
        </div>

        <nav>
          {menu.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'active' : ''}`
              }
            >
              <Icon size={17} strokeWidth={1.8} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="sidebar-bottom">
        <div className="sidebar-section">
          <div className="sidebar-section-title">
            Система
          </div>

          <div className="sidebar-link">
            <Settings size={17} strokeWidth={1.8} />
            <span>Настройки</span>
          </div>
        </div>

        <div
          style={{
            padding: '14px 10px',
            borderTop: '1px solid rgba(0,0,0,0.07)',
            color: '#aaa',
            fontSize: 10,
          }}
        >
          DISPATCHAI · 0.3.0
        </div>
      </div>
    </aside>
  )
}