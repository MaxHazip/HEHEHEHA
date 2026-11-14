import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Здесь обязательно должна быть роль 'engineer'
export type Role = 'client' | 'dispatcher' | 'engineer' | null

export interface UserProfile {
  name: string
  phone: string
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
      logout: () => set({ role: null, user: null }),
    }),
    { name: 'auth-storage' }
  )
)