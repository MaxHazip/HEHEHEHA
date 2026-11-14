import { api } from '@/lib/api'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Добавили роль 'admin'
export type Role = 'client' | 'dispatcher' | 'engineer' | 'admin' | null

export interface UserProfile {
  name: string
  phone: string
  engineerId?: number | null
  role: Role
}

interface AuthState {
  role: Role
  user: UserProfile | null
  login: (user: UserProfile) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      role: null,
      user: null,
      login: (user) => set({ role: user.role, user }),
      logout: () => {
        void api.post('/api/users/logout').catch(() => undefined)
        set({ role: null, user: null })
      },
    }),
    { name: 'dispatchai-auth-v3' }
  )
)