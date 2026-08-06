import React from "react"
import { useNavigate, Link } from "react-router-dom"
import { UserPlus } from "lucide-react"
import { authApi, type RegisterRequest } from "@/features/auth/api/auth-api"
import { useAuthStore } from "@/stores/auth-store"
import { ApiError } from "@/lib/api-client"

export function RegisterForm() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const setToken = useAuthStore((s) => s.setToken)

  const [email, setEmail] = React.useState("")
  const [password, setPassword] = React.useState("")
  const [fullName, setFullName] = React.useState("")
  const [error, setError] = React.useState<string | null>(null)
  const [isLoading, setIsLoading] = React.useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      const registerData: RegisterRequest = {
        email,
        password,
        full_name: fullName.trim() || undefined,
      }
      const authResponse = await authApi.register(registerData)

      // Persist the token first so GET /me carries the bearer header
      setToken(authResponse.access_token)

      // Fetch user profile
      const user = await authApi.getMe()

      // Store auth state
      setAuth(authResponse.access_token, user)

      // Redirect to dashboard
      navigate("/app/dashboard")
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError("注册失败，请稍后重试")
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <div style={styles.header}>
        <div style={styles.iconWrapper}>
          <UserPlus size={20} />
        </div>
        <h2 style={styles.title}>注册问鉴账号</h2>
        <p style={styles.subtitle}>创建账号开始使用面试训练系统</p>
      </div>

      {error && (
        <div style={styles.errorBanner}>
          <div style={styles.errorText}>{error}</div>
        </div>
      )}

      <div style={styles.fieldGroup}>
        <label htmlFor="fullName" style={styles.label}>
          姓名 <span style={styles.optional}>(可选)</span>
        </label>
        <input
          id="fullName"
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          autoComplete="name"
          placeholder="张三"
          style={styles.input}
          disabled={isLoading}
        />
      </div>

      <div style={styles.fieldGroup}>
        <label htmlFor="email" style={styles.label}>
          邮箱地址
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
          placeholder="your@email.com"
          style={styles.input}
          disabled={isLoading}
        />
      </div>

      <div style={styles.fieldGroup}>
        <label htmlFor="password" style={styles.label}>
          密码
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="new-password"
          placeholder="至少 8 个字符"
          minLength={8}
          style={styles.input}
          disabled={isLoading}
        />
        <div style={styles.hint}>密码长度至少 8 个字符</div>
      </div>

      <button type="submit" className="btn-primary" style={styles.submitButton} disabled={isLoading}>
        {isLoading ? "注册中..." : "注册"}
      </button>

      <div style={styles.footer}>
        <span style={styles.footerText}>已有账号？</span>
        <Link to="/login" style={styles.link}>
          立即登录
        </Link>
      </div>
    </form>
  )
}

const styles: Record<string, React.CSSProperties> = {
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "1.25rem",
  },
  header: {
    textAlign: "center" as const,
    marginBottom: "0.5rem",
  },
  iconWrapper: {
    width: 48,
    height: 48,
    borderRadius: 16,
    background: "var(--wj-brand-accent-bg)",
    color: "var(--wj-brand-secondary)",
    display: "inline-grid",
    placeItems: "center",
    marginBottom: "1rem",
  },
  title: {
    margin: 0,
    fontSize: "1.5rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
  },
  subtitle: {
    margin: "0.5rem 0 0",
    fontSize: "0.9rem",
    color: "var(--wj-text-secondary)",
  },
  errorBanner: {
    padding: "0.85rem 1rem",
    borderRadius: 12,
    background: "var(--wj-danger-bg)",
    border: "1px solid var(--wj-danger-border)",
  },
  errorText: {
    fontSize: "0.875rem",
    color: "var(--wj-danger-text)",
    margin: 0,
  },
  fieldGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "0.5rem",
  },
  label: {
    fontSize: "0.875rem",
    fontWeight: 500,
    color: "var(--wj-text-primary)",
  },
  optional: {
    fontWeight: 400,
    color: "var(--wj-text-secondary)",
  },
  input: {
    padding: "0.75rem 1rem",
    fontSize: "0.95rem",
    borderRadius: 12,
    border: "1px solid var(--wj-border-default)",
    background: "var(--wj-bg-surface)",
    color: "var(--wj-text-primary)",
    transition: "border-color 0.2s, box-shadow 0.2s",
    outline: "none",
  },
  hint: {
    fontSize: "0.8rem",
    color: "var(--wj-text-secondary)",
    marginTop: "-0.25rem",
  },
  submitButton: {
    marginTop: "0.5rem",
  },
  footer: {
    textAlign: "center" as const,
    fontSize: "0.875rem",
  },
  footerText: {
    color: "var(--wj-text-secondary)",
    marginRight: "0.5rem",
  },
  link: {
    color: "var(--wj-brand-secondary)",
    textDecoration: "none",
    fontWeight: 500,
  },
}
