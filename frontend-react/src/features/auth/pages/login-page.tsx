import { Link } from "react-router-dom"
import { ArrowRight, FileUp, LayoutDashboard, MessageSquareText } from "lucide-react"
import { BrandIntro } from "@/components/brand/BrandLogo"
import { usePageTitle } from "@/lib/use-page-title"

const actions = [
  {
    title: "进入工作台",
    description: "查看未完成的模拟面试、最近简历和下一步训练建议。",
    to: "/app/dashboard",
    icon: LayoutDashboard,
    primary: true,
  },
  {
    title: "上传简历",
    description: "从一份真实简历开始，让问鉴生成更贴合经历的问题。",
    to: "/app/resumes/new",
    icon: FileUp,
  },
  {
    title: "继续模拟面试",
    description: "回到已有面试记录，延续上下文完成连续追问。",
    to: "/app/interviews",
    icon: MessageSquareText,
  },
]

export default function LoginPage() {
  usePageTitle("/login")

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "2rem",
      }}
    >
      <div
        style={{
          width: "min(1120px, 100%)",
          display: "grid",
          gridTemplateColumns: "minmax(0, 1.15fr) minmax(360px, 0.85fr)",
          gap: "1.5rem",
          alignItems: "stretch",
        }}
      >
        <section className="app-surface" style={{ padding: "2.5rem 2.5rem 2.25rem" }}>
          <BrandIntro />
          <div
            className="app-muted-surface"
            style={{
              marginTop: "1.75rem",
              padding: "1.15rem 1.2rem",
              display: "grid",
              gap: "0.5rem",
            }}
          >
            <div className="app-eyebrow">Product Positioning</div>
            <p style={{ margin: 0, color: "var(--wj-text-primary)", fontSize: "0.96rem", lineHeight: 1.75 }}>
              问鉴不是普通题库，也不是通用聊天页面。它围绕真实简历、回答表现与证据一致性来组织训练流程，
              重点支持连续追问、回答评分、能力分析、报告生成与面试恢复。
            </p>
          </div>
        </section>

        <section className="app-surface" style={{ padding: "1.7rem" }}>
          <div className="app-eyebrow">Choose Your Next Step</div>
          <h2 style={{ margin: "0.45rem 0 0", fontSize: "1.35rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
            直接进入真实业务流程
          </h2>
          <p style={{ margin: "0.55rem 0 0", color: "var(--wj-text-secondary)", lineHeight: 1.7 }}>
            当前项目没有完整登录链路，因此这里保留为品牌入口页，不虚构注册或认证接口。
          </p>

          <div style={{ display: "grid", gap: "0.85rem", marginTop: "1.4rem" }}>
            {actions.map((action) => {
              const Icon = action.icon
              return (
                <Link
                  key={action.title}
                  to={action.to}
                  className={action.primary ? "btn-primary" : undefined}
                  style={{
                    padding: "1rem 1rem 1rem 1.05rem",
                    borderRadius: 16,
                    border: action.primary ? undefined : "1px solid var(--wj-border-default)",
                    background: action.primary ? undefined : "var(--wj-bg-surface)",
                    color: action.primary ? undefined : "var(--wj-text-primary)",
                    display: "grid",
                    gridTemplateColumns: "auto 1fr auto",
                    gap: "0.8rem",
                    alignItems: "center",
                    boxShadow: action.primary ? undefined : "var(--wj-shadow-sm)",
                  }}
                >
                  <div
                    style={{
                      width: 42,
                      height: 42,
                      borderRadius: 14,
                      background: action.primary ? "rgba(255,255,255,0.12)" : "var(--wj-brand-accent-bg)",
                      color: action.primary ? "#ffffff" : "var(--wj-brand-secondary)",
                      display: "grid",
                      placeItems: "center",
                    }}
                  >
                    <Icon size={18} />
                  </div>
                  <div>
                    <div style={{ fontSize: "0.95rem", fontWeight: 600 }}>{action.title}</div>
                    <div
                      style={{
                        marginTop: "0.3rem",
                        fontSize: "0.82rem",
                        lineHeight: 1.55,
                        color: action.primary ? "rgba(255,255,255,0.82)" : "var(--wj-text-secondary)",
                      }}
                    >
                      {action.description}
                    </div>
                  </div>
                  <ArrowRight size={18} />
                </Link>
              )
            })}
          </div>
        </section>
      </div>
    </div>
  )
}
