import { useAuthStore } from '@/store/authStore'
import {
  LogOut,
  Bell,
  Search,
} from 'lucide-react'

export default function Topbar() {
  const { logout, user, role } = useAuthStore()

  const roleLabels: Record<string, string> = {
    dispatcher: 'Диспетчер',
    engineer: 'Инженер',
    admin: 'Администратор',
    client: 'Клиент',
  }

  const initials = user?.name
    ? user.name.charAt(0).toUpperCase()
    : 'U'

  return (
    <header className="app-topbar">
      <div>
        <div
          style={{
            color: '#999',
            fontSize: 11,
            marginBottom: 4,
          }}
        >
          DISPATCHAI / WORKSPACE
        </div>

        <div
          style={{
            fontSize: 15,
            fontWeight: 600,
            letterSpacing: '-0.4px',
          }}
        >
          {roleLabels[role || ''] || 'Пользователь'}
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}
      >
        <button
          className="app-topbar-button"
          title="Поиск"
          type="button"
        >
          <Search size={17} strokeWidth={1.7} />
        </button>

        <button
          className="app-topbar-button"
          title="Уведомления"
          type="button"
        >
          <Bell size={17} strokeWidth={1.7} />
        </button>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            marginLeft: 8,
            paddingLeft: 12,
            borderLeft: '1px solid rgba(0,0,0,0.09)',
          }}
        >
          <div className="app-topbar-avatar">
            {initials}
          </div>

          <div className="hidden sm:block">
            <div
              style={{
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              {user?.name || 'Пользователь'}
            </div>

            <div
              style={{
                color: '#999',
                fontSize: 10,
                marginTop: 2,
              }}
            >
              {user?.phone || ''}
            </div>
          </div>
        </div>

        <button
          className="app-topbar-button"
          onClick={logout}
          title="Выйти"
          type="button"
        >
          <LogOut size={17} strokeWidth={1.7} />
        </button>
      </div>
    </header>
  )
}