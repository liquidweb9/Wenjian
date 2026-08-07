import type { ReactNode } from "react"
import { BrandMark } from "@/components/brand/BrandLogo"
import { BackButton } from "@/components/common/back-button"

interface PageHeaderProps {
  title: string
  description?: string
  action?: ReactNode
  brand?: boolean
  back?: { to: string; label?: string }
}

export function PageHeader({ title, description, action, brand = false, back }: PageHeaderProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: "1rem",
        marginBottom: "1.5rem",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem", minWidth: 0 }}>
        {back ? <BackButton to={back.to} label={back.label} /> : null}
        <div style={{ display: "flex", gap: brand ? "0.85rem" : 0, alignItems: "flex-start" }}>
          {brand ? <BrandMark size={28} /> : null}
          <div>
            {brand ? <div className="app-eyebrow">Wenjian</div> : null}
            <h1
              style={{
                margin: brand ? "0.35rem 0 0" : 0,
                fontSize: "1.55rem",
                lineHeight: 1.25,
                fontWeight: 600,
                color: "var(--wj-text-primary)",
              }}
            >
              {title}
            </h1>
            {description ? (
              <p
                style={{
                  margin: "0.55rem 0 0",
                  color: "var(--wj-text-secondary)",
                  fontSize: "0.92rem",
                  lineHeight: 1.7,
                  maxWidth: 760,
                }}
              >
                {description}
              </p>
            ) : null}
          </div>
        </div>
      </div>
      {action ? <div style={{ flexShrink: 0 }}>{action}</div> : null}
    </div>
  )
}
