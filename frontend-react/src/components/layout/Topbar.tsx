import { useLocation, useNavigate } from "react-router-dom"
import { Menu, UserRound, LogOut } from "lucide-react"
import { useUIStore } from "@/stores/ui-store"
import { useAuthStore } from "@/stores/auth-store"
import { PAGE_TITLES } from "@/lib/brand"
import React from "react"

function getCurrentTitle(pathname: string) {
  const matches = Object.entries(PAGE_TITLES)
    .filter(([path]) => path !== "/login" && pathname.startsWith(path))
    .sort((a, b) => b[0].length - a[0].length)

  return matches[0]?.[1] ?? "工作台"
}

export function Topbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const toggleSidebar = useUIStore((state) => state.toggleSidebar)
  const user = useAuthStore((s) => s.user)
  const clearAuth = useAuthStore((s) => s.clearAuth)
  const title = getCurrentTitle(location.pathname)
  const [showUserMenu, setShowUserMenu] = React.useState(false)

  const handleLogout = () => {
    clearAuth()
    navigate("/login")
  }

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

      <div style={{ position: "relative" }}>
        <button
          onClick={() => setShowUserMenu(!showUserMenu)}
          className="app-muted-surface"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.65rem",
            padding: "0.55rem 0.8rem",
            color: "var(--wj-text-secondary)",
            border: "none",
            cursor: "pointer",
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
          <div style={{ fontSize: "0.82rem", lineHeight: 1.3, textAlign: "left" }}>
            <div style={{ fontWeight: 600, color: "var(--wj-text-primary)" }}>
              {user?.full_name || user?.email || "候选人工作区"}
            </div>
            <div>{user?.email || "围绕真实经历完成训练"}</div>
          </div>
        </button>

        {showUserMenu && (
          <>
            <div
              style={{
                position: "fixed",
                inset: 0,
                zIndex: 19,
              }}
              onClick={() => setShowUserMenu(false)}
            />
            <div
              className="app-surface"
              style={{
                position: "absolute",
                top: "calc(100% + 0.5rem)",
                right: 0,
                zIndex: 20,
                minWidth: 200,
                padding: "0.5rem",
                boxShadow: "var(--wj-shadow-lg)",
                borderRadius: 12,
              }}
            >
              <button
                onClick={handleLogout}
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  padding: "0.65rem 0.75rem",
                  fontSize: "0.9rem",
                  color: "var(--wj-text-primary)",
                  background: "transparent",
                  border: "none",
                  borderRadius: 8,
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "background 0.15s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--wj-bg-muted)"
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent"
                }}
              >
                <LogOut size={16} />
                <span>退出登录</span>
              </button>
            </div>
          </>
        )}
      </div>
    </header>
  )
}
