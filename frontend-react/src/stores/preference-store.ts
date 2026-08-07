import { create } from "zustand"
import { persist } from "zustand/middleware"

export type ModelTier = "auto" | "fast" | "balanced" | "judge"

interface PreferenceState {
  defaultMode: string
  defaultMaxTurns: number
  coachingEnabled: boolean
  defaultModelTier: ModelTier
  setDefaultMode: (mode: string) => void
  setDefaultMaxTurns: (n: number) => void
  setCoachingEnabled: (v: boolean) => void
  setDefaultModelTier: (tier: ModelTier) => void
}

export const usePreferenceStore = create<PreferenceState>()(
  persist(
    (set) => ({
      defaultMode: "simulation",
      defaultMaxTurns: 15,
      coachingEnabled: true,
      defaultModelTier: "auto",
      setDefaultMode: (mode) => set({ defaultMode: mode }),
      setDefaultMaxTurns: (n) => set({ defaultMaxTurns: n }),
      setCoachingEnabled: (v) => set({ coachingEnabled: v }),
      setDefaultModelTier: (tier) => set({ defaultModelTier: tier }),
    }),
    { name: "preferences" },
  ),
)
