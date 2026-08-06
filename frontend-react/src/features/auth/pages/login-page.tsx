import { BrandIntro } from "@/components/brand/BrandLogo"
import { usePageTitle } from "@/lib/use-page-title"
import { LoginForm } from "@/features/auth/components/login-form"

export default function LoginPage() {
  usePageTitle("登录")

  return (
    <div style={styles.container}>
      <div style={styles.wrapper}>
        <section className="app-surface" style={styles.brandSection}>
          <BrandIntro />
          <div className="app-muted-surface" style={styles.positioning}>
            <div className="app-eyebrow">Product Positioning</div>
            <p style={styles.positioningText}>
              问鉴不是普通题库，也不是通用聊天页面。它围绕真实简历、回答表现与证据一致性来组织训练流程，
              重点支持连续追问、回答评分、能力分析、报告生成与面试恢复。
            </p>
          </div>
        </section>

        <section className="app-surface" style={styles.formSection}>
          <LoginForm />
        </section>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: "100vh",
    display: "grid",
    placeItems: "center",
    padding: "2rem",
  },
  wrapper: {
    width: "min(1120px, 100%)",
    display: "grid",
    gridTemplateColumns: "minmax(0, 1.15fr) minmax(360px, 0.85fr)",
    gap: "1.5rem",
    alignItems: "stretch",
  },
  brandSection: {
    padding: "2.5rem 2.5rem 2.25rem",
  },
  positioning: {
    marginTop: "1.75rem",
    padding: "1.15rem 1.2rem",
    display: "grid",
    gap: "0.5rem",
  },
  positioningText: {
    margin: 0,
    color: "var(--wj-text-primary)",
    fontSize: "0.96rem",
    lineHeight: 1.75,
  },
  formSection: {
    padding: "2rem",
  },
}
