interface LoadingStateProps {
  rows?: number
  message?: string
}

export function LoadingState({
  rows = 4,
  message = "问鉴正在准备内容，请稍候。",
}: LoadingStateProps) {
  return (
    <div style={{ padding: "2rem 0" }}>
      <div className="app-surface" style={{ padding: "1.5rem", maxWidth: 720 }}>
        {Array.from({ length: rows }, (_, index) => (
          <div
            key={index}
            style={{
              height: index === 0 ? 16 : 13,
              width: index === 0 ? "36%" : index === rows - 1 ? "56%" : "100%",
              backgroundColor: "var(--wj-bg-subtle)",
              borderRadius: 999,
              marginBottom: index < rows - 1 ? "0.85rem" : 0,
              animation: "pulse 1.2s ease-in-out infinite",
              animationDelay: `${index * 0.12}s`,
            }}
          />
        ))}
      </div>
      <p style={{ margin: "0.9rem 0 0", color: "var(--wj-text-secondary)", fontSize: "0.86rem" }}>{message}</p>
    </div>
  )
}
