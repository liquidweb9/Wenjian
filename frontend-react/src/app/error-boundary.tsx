import { Component, type ReactNode } from "react"

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class AppErrorBoundary extends Component<Props, State> {
  override state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  override render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div style={{ padding: "2rem", textAlign: "center" }}>
            <div style={{ textAlign: "center", color: "#475569", marginBottom: "1rem" }}>
              <h2 style={{ color: "#0d1b2a", fontSize: "1.25rem", fontWeight: 600 }}>本次分析未能完成</h2>
              <p style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>你的面试和回答数据不会因此丢失，请重新尝试。</p>
            </div>
            {this.state.error && (
              <p style={{ color: "#64748b", margin: "0.5rem 0", fontSize: "0.8rem" }}>
                {this.state.error.message}
              </p>
            )}
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null })
                window.location.reload()
              }}
              style={{
                padding: "0.5rem 1.5rem",
                backgroundColor: "#0d1b2a",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "0.9rem",
              }}
            >
              重新加载
            </button>
          </div>
        )
      )
    }
    return this.props.children
  }
}
