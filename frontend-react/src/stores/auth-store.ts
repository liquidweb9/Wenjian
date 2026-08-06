import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { User } from "@/features/auth/api/auth-api"

interface AuthState {
  // State
  token: string | null
  user: User | null
  isAuthenticated: boolean

  // Actions
  setAuth: (token: string, user: User) => void
  setToken: (token: string) => void
  clearAuth: () => void
  updateUser: (user: User) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Initial state
      token: null,
      user: null,
      isAuthenticated: false,

      // Set authentication (after login/register)
      setAuth: (token, user) =>
        set({
          token,
          user,
          isAuthenticated: true,
        }),

      // Persist the token before fetching the profile so subsequent requests
      // (e.g. GET /me) carry the bearer header.
      setToken: (token) =>
        set({
          token,
          isAuthenticated: true,
        }),

      // Clear authentication (logout)
      clearAuth: () =>
        set({
          token: null,
          user: null,
          isAuthenticated: false,
        }),

      // Update user profile
      updateUser: (user) =>
        set((state) => ({
          user,
          isAuthenticated: state.isAuthenticated,
        })),
    }),
    {
      name: "auth-storage",
      // Only persist token and user, not computed isAuthenticated
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
      // Derive isAuthenticated from the persisted token during hydration.
      // (Avoids self-referencing the store from onRehydrateStorage, which runs
      // before the store is assigned and would throw in the TDZ.)
      merge: (persisted, current) => {
        const p = (persisted ?? {}) as { token?: string | null; user?: User | null }
        return {
          ...current,
          token: p.token ?? null,
          user: p.user ?? null,
          isAuthenticated: Boolean(p.token),
        }
      },
    },
  ),
)
