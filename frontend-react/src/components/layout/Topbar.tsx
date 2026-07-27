import { useLocation } from "react-router-dom"
import { Menu, UserRound } from "lucide-react"
import { useUIStore } from "@/stores/ui-store"
import { PAGE_TITLES } from "@/lib/brand"

function getCurrentTitle(pathname: string) {
  const matches = Object.entries(PAGE_TITLES)
    .filter(([path]) => path !== "/login" && pathname.startsWith(path))
    .sort((a, b) => b[0].length - a[0].length)

  return matches[0]?.[1] ?? "工作台"
}

export function Topbar() {
  const location = useLocation()
  const toggleSidebar = useUIStore((state) => state.toggleSidebar)
  const title = getCurrentTitle(location.pathname)

  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 10,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "1rem",
        padding: "1rem 1.5rem",
        background: "rgb(247 248 250 / 88%)",
        backdropFilter: "blur(16px)",
        borderBottom: "1px solid var(--wj-border-subtle)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.95rem" }}>
        <button
          onClick={toggleSidebar}
          aria-label="切换侧边栏"
          style={{
            width: 40,
            height: 40,
            borderRadius: 12,
            border: "1px solid var(--wj-border-default)",
            background: "var(--wj-bg-surface)",
            color: "var(--wj-text-secondary)",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Menu size={18} />
        </button>

        <div>
          <div className="app-eyebrow">Wenjian Workspace</div>
          <h1 style={{ margin: "0.25rem 0 0", fontSize: "1.15rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
            {title}
          </h1>
        </div>
      </div>

      <div
        className="app-muted-surface"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.65rem",
          padding: "0.55rem 0.8rem",
          color: "var(--wj-text-secondary)",
        }}
      >
        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: 12,
            background: "var(--wj-brand-accent-bg)",
            color: "var(--wj-brand-secondary)",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <UserRound size={16} />
        </div>
        <div style={{ fontSize: "0.82rem", lineHeight: 1.3 }}>
          <div style={{ fontWeight: 600, color: "var(--wj-text-primary)" }}>候选人工作区</div>
          <div>围绕真实经历完成训练</div>
        </div>
      </div>
    </header>
  )
}
