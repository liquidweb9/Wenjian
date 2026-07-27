import { BrandMark } from "@/components/brand/BrandLogo"

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
  brand?: boolean
}

export function ErrorState({
  title,
  message,
  onRetry,
  brand = false,
}: ErrorStateProps) {
  const resolvedTitle = title ?? (brand ? "本次分析未能完成" : "页面内容暂时无法加载")
  const resolvedMessage =
    message ??
    (brand
      ? "你的面试和回答数据不会因此丢失，请重新尝试。"
      : "请检查网络连接后重新尝试，或稍后回到问鉴继续。")

  return (
    <section
      className="app-surface"
      style={{
        maxWidth: 560,
        margin: "0 auto",
        padding: "2.5rem 2rem",
        textAlign: "center",
      }}
    >
      <div style={{ display: "flex", justifyContent: "center" }}>
        <BrandMark size={42} />
      </div>
      <h2 style={{ margin: "1rem 0 0", fontSize: "1.08rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
        {resolvedTitle}
      </h2>
      <p style={{ margin: "0.6rem auto 0", maxWidth: 420, color: "var(--wj-text-secondary)", lineHeight: 1.7 }}>
        {resolvedMessage}
      </p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="btn-primary"
          style={{ marginTop: "1.35rem" }}
        >
          重新尝试
        </button>
      ) : null}
    </section>
  )
}
