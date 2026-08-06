import { NavLink, useLocation } from "react-router-dom"
import { LayoutDashboard, FileText, MessageSquare, Target, BarChart3, Settings } from "lucide-react"
import { useUIStore } from "@/stores/ui-store"
import { BrandLogo } from "@/components/brand/BrandLogo"

const navItems = [
  { to: "/app/dashboard", label: "工作台", description: "继续训练与下一步操作", icon: LayoutDashboard },
  { to: "/app/resumes", label: "简历管理", description: "上传、确认与查看资料", icon: FileText },
  { to: "/app/job-targets", label: "目标岗位", description: "定义岗位与能力需求", icon: Target },
  { to: "/app/interviews", label: "模拟面试", description: "开始、继续或查看记录", icon: MessageSquare },
  { to: "/app/analytics", label: "能力分析", description: "查看趋势与评估结果", icon: BarChart3 },
  { to: "/app/settings", label: "设置", description: "偏好与系统选项", icon: Settings },
]

export function Sidebar() {
  const collapsed = useUIStore((state) => state.sidebarCollapsed)
  const location = useLocation()

  return (
    <aside
      style={{
        width: collapsed ? "var(--wj-sidebar-collapsed-width)" : "var(--wj-sidebar-width)",
        transition: "width 180ms ease",
        background:
          "linear-gradient(180deg, rgba(13, 27, 42, 0.98) 0%, rgba(15, 34, 52, 0.98) 100%)",
        color: "#fff",
        display: "flex",
        flexDirection: "column",
        borderRight: "1px solid rgba(255,255,255,0.06)",
        height: "100dvh",
        flexShrink: 0,
        overflow: "hidden",
        position: "sticky",
        top: 0,
      }}
    >
      <div
        style={{
          padding: collapsed ? "1rem 0.75rem" : "1.25rem 1.1rem 1rem",
          borderBottom: "1px solid rgba(255,255,255,0.08)",
        }}
      >
        <BrandLogo collapsed={collapsed} variant="dark" />
        {!collapsed && (
          <p
            style={{
              margin: "0.8rem 0 0",
              color: "rgba(226, 232, 240, 0.72)",
              fontSize: "0.76rem",
              lineHeight: 1.65,
            }}
          >
            从真实简历出发，完成连续追问、回答评分与证据分析。
          </p>
        )}
      </div>

      <nav style={{ padding: "0.75rem 0.65rem", display: "grid", gap: "0.35rem", overflow: "hidden" }}>
        {navItems.map((item) => {
          const active = location.pathname.startsWith(item.to)
          const Icon = item.icon

          return (
            <NavLink
              key={item.to}
              to={item.to}
              title={collapsed ? `${item.label} | 问鉴 Wenjian` : undefined}
              style={{
                display: "flex",
                alignItems: collapsed ? "center" : "flex-start",
                justifyContent: collapsed ? "center" : "flex-start",
                gap: collapsed ? 0 : "0.85rem",
                padding: collapsed ? "0.85rem 0.35rem" : "0.85rem 0.9rem",
                borderRadius: 14,
                textDecoration: "none",
                background: active ? "rgba(255,255,255,0.08)" : "transparent",
                color: active ? "#ffffff" : "rgba(226, 232, 240, 0.72)",
                border: active ? "1px solid rgba(34,193,195,0.35)" : "1px solid transparent",
                transition: "background-color 180ms ease, border-color 180ms ease, color 180ms ease",
              }}
            >
              <Icon
                size={18}
                style={{
                  flexShrink: 0,
                  color: active ? "var(--wj-brand-accent)" : "rgba(226, 232, 240, 0.68)",
                  marginTop: collapsed ? 0 : 2,
                }}
              />
              {!collapsed && (
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: "0.92rem", fontWeight: 600, lineHeight: 1.2 }}>{item.label}</div>
                  <div style={{ fontSize: "0.73rem", lineHeight: 1.45, marginTop: "0.28rem" }}>
                    {item.description}
                  </div>
                </div>
              )}
            </NavLink>
          )
        })}
      </nav>
    </aside>
  )
}
