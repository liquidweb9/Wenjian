import { create } from "zustand"
import { persist } from "zustand/middleware"

interface PreferenceState {
  defaultMode: string
  defaultMaxTurns: number
  coachingEnabled: boolean
  setDefaultMode: (mode: string) => void
  setDefaultMaxTurns: (n: number) => void
  setCoachingEnabled: (v: boolean) => void
}

export const usePreferenceStore = create<PreferenceState>()(
  persist(
    (set) => ({
      defaultMode: "simulation",
      defaultMaxTurns: 15,
      coachingEnabled: true,
      setDefaultMode: (mode) => set({ defaultMode: mode }),
      setDefaultMaxTurns: (n) => set({ defaultMaxTurns: n }),
      setCoachingEnabled: (v) => set({ coachingEnabled: v }),
    }),
    { name: "preferences" },
  ),
)
