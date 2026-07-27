import { create } from "zustand"
import { persist } from "zustand/middleware"

interface UIState {
  sidebarCollapsed: boolean
  theme: "light" | "dark"
  interviewPanelWidth: number
  toggleSidebar: () => void
  setTheme: (theme: "light" | "dark") => void
  setInterviewPanelWidth: (w: number) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      theme: "light",
      interviewPanelWidth: 320,
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setTheme: (theme) => set({ theme }),
      setInterviewPanelWidth: (w) => set({ interviewPanelWidth: w }),
    }),
    { name: "ui-store" },
  ),
)
