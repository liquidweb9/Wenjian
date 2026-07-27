import type { ReactNode } from "react"
import { BrandMark } from "@/components/brand/BrandLogo"

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description: string
  action?: ReactNode
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <section
      className="app-surface"
      style={{
        padding: "2.5rem 2rem",
        textAlign: "center",
        maxWidth: 560,
        margin: "0 auto",
      }}
    >
      <div style={{ display: "flex", justifyContent: "center" }}>{icon || <BrandMark size={42} />}</div>
      <h2 style={{ margin: "1.1rem 0 0", fontSize: "1.1rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
        {title}
      </h2>
      <p
        style={{
          margin: "0.6rem auto 0",
          maxWidth: 420,
          color: "var(--wj-text-secondary)",
          fontSize: "0.9rem",
          lineHeight: 1.7,
        }}
      >
        {description}
      </p>
      {action ? <div style={{ marginTop: "1.4rem" }}>{action}</div> : null}
    </section>
  )
}
