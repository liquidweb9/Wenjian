import { BrandMark } from "@/components/brand/BrandLogo"
import { BRAND } from "@/lib/brand"

interface WelcomePanelProps {
  userName?: string
}

function getGreetingByHour(hour: number) {
  if (hour < 12) return "早上好"
  if (hour < 18) return "下午好"
  return "晚上好"
}

export function WelcomePanel({ userName }: WelcomePanelProps) {
  const greeting = getGreetingByHour(new Date().getHours())

  return (
    <section
      className="app-surface"
      style={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 1fr) auto",
        gap: "1.5rem",
        padding: "1.4rem 1.5rem",
        marginBottom: "1.5rem",
      }}
    >
      <div style={{ display: "flex", gap: "0.9rem", alignItems: "flex-start" }}>
        <BrandMark size={34} />
        <div>
          <div className="app-eyebrow">Wenjian Workspace</div>
          <h2 style={{ margin: "0.4rem 0 0", fontSize: "1.38rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
            {greeting}
            {userName ? `，${userName}` : ""}，欢迎回到问鉴
          </h2>
          <p style={{ margin: "0.55rem 0 0", color: "var(--wj-text-primary)", fontSize: "0.98rem", fontWeight: 500 }}>
            {BRAND.tagline}
          </p>
          <p style={{ margin: "0.45rem 0 0", color: "var(--wj-text-secondary)", fontSize: "0.9rem", lineHeight: 1.7 }}>
            继续完成你的面试训练，或从一份新的真实简历开始。首页内容仍以待办任务、简历与面试进度为中心。
          </p>
        </div>
      </div>

      <div
        className="app-muted-surface"
        style={{
          display: "grid",
          alignContent: "center",
          gap: "0.35rem",
          padding: "0.95rem 1rem",
          minWidth: 200,
        }}
      >
        <span style={{ fontSize: "0.76rem", color: "var(--wj-text-tertiary)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          今日建议
        </span>
        <span style={{ fontSize: "0.92rem", color: "var(--wj-text-primary)", fontWeight: 600 }}>
          优先继续未完成的模拟面试
        </span>
        <span style={{ fontSize: "0.83rem", color: "var(--wj-text-secondary)" }}>
          保持问题上下文连续，训练反馈会更完整。
        </span>
      </div>
    </section>
  )
}
