import { BrandIntro } from "@/components/brand/BrandLogo"
import { usePageTitle } from "@/lib/use-page-title"
import { RegisterForm } from "@/features/auth/components/register-form"

export default function RegisterPage() {
  usePageTitle("注册")

  return (
    <div style={styles.container}>
      <div style={styles.wrapper}>
        <section className="app-surface" style={styles.brandSection}>
          <BrandIntro />
          <div className="app-muted-surface" style={styles.positioning}>
            <div className="app-eyebrow">Why Choose Wenjian</div>
            <p style={styles.positioningText}>
              问鉴提供证据驱动的面试训练系统，围绕目标岗位验证简历 Claim、追踪证据链，
              通过多场面试检验能力迁移，生成个性化训练计划。
            </p>
          </div>
        </section>

        <section className="app-surface" style={styles.formSection}>
          <RegisterForm />
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
