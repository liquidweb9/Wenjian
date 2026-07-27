import { Link } from "react-router-dom"
import markSvg from "@/assets/brand/wenjian-mark.svg"
import markDarkSvg from "@/assets/brand/wenjian-mark-dark.svg"
import { BRAND } from "@/lib/brand"

interface BrandLogoProps {
  collapsed?: boolean
  linkTo?: string
  variant?: "light" | "dark"
  size?: number
}

export function BrandLogo({
  collapsed = false,
  linkTo = "/app/dashboard",
  variant = "light",
  size = 40,
}: BrandLogoProps) {
  const mark = variant === "dark" ? markDarkSvg : markSvg
  const foreground = variant === "dark" ? "#ffffff" : "var(--wj-brand-primary)"
  const secondary = variant === "dark" ? "rgba(226, 232, 240, 0.78)" : "var(--wj-text-secondary)"

  return (
    <Link
      to={linkTo}
      aria-label={BRAND.alt}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: collapsed ? "center" : "flex-start",
        textDecoration: "none",
        minWidth: 0,
      }}
    >
      {collapsed ? (
        <img
          src={mark}
          alt={BRAND.alt}
          width={32}
          height={32}
          style={{ width: 36, height: 32, objectFit: "contain" }}
        />
      ) : (
        <>
          <img
            src={mark}
            alt=""
            width={Math.round(size * 1.35)}
            height={size}
            style={{ width: Math.round(size * 1.35), height: size, objectFit: "contain", flexShrink: 0 }}
          />
          <span style={{ display: "flex", alignItems: "baseline", gap: "0.55rem", minWidth: 0 }}>
            <span style={{ color: foreground, fontSize: Math.round(size * 0.7), lineHeight: 1, fontWeight: 750, letterSpacing: "-0.03em" }}>
              Wenjian
            </span>
            <span style={{ color: secondary, fontFamily: '"Noto Serif SC", "Songti SC", serif', fontSize: Math.round(size * 0.42), fontWeight: 600 }}>
              问鉴
            </span>
          </span>
        </>
      )}
    </Link>
  )
}

export function BrandMark({ size = 40 }: { size?: number }) {
  return (
    <img
      src={markSvg}
      alt={BRAND.alt}
      width={size}
      height={size}
      style={{ width: size * 1.35, height: size, objectFit: "contain" }}
    />
  )
}

export function BrandIntro({ compact = false }: { compact?: boolean }) {
  return (
    <div style={{ maxWidth: compact ? 420 : 520 }}>
      <div style={{ display: "flex", alignItems: "center", gap: compact ? "0.85rem" : "1rem" }}>
        <BrandMark size={compact ? 44 : 56} />
        <div>
          <div
            style={{
              color: "var(--wj-text-primary)",
              fontSize: compact ? "1.55rem" : "1.95rem",
              lineHeight: 1.15,
              fontWeight: 700,
            }}
          >
            {BRAND.chineseName}
          </div>
          <div
            style={{
              color: "var(--wj-text-secondary)",
              fontSize: compact ? "0.95rem" : "1.05rem",
              letterSpacing: "0.04em",
              marginTop: "0.15rem",
            }}
          >
            {BRAND.englishName}
          </div>
        </div>
      </div>

      <p
        style={{
          margin: compact ? "1rem 0 0" : "1.35rem 0 0",
          color: "var(--wj-brand-secondary)",
          fontSize: compact ? "0.76rem" : "0.8rem",
          fontWeight: 700,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
        }}
      >
        Resume-grounded AI Interview Platform
      </p>
      <h1
        style={{
          margin: "0.45rem 0 0",
          color: "var(--wj-text-primary)",
          fontSize: compact ? "1.25rem" : "1.8rem",
          lineHeight: 1.3,
          fontWeight: 600,
        }}
      >
        简历驱动的 AI 模拟面试平台
      </h1>
      <p
        style={{
          margin: "0.75rem 0 0",
          color: "var(--wj-text-primary)",
          fontSize: compact ? "0.95rem" : "1.05rem",
          lineHeight: 1.65,
          fontWeight: 500,
        }}
      >
        {BRAND.tagline}
      </p>
      <p
        style={{
          margin: "0.75rem 0 0",
          color: "var(--wj-text-secondary)",
          fontSize: compact ? "0.88rem" : "0.95rem",
          lineHeight: 1.75,
        }}
      >
        {BRAND.summary}
      </p>
    </div>
  )
}
