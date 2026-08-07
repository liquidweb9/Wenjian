import { ArrowLeft } from "lucide-react"
import { useNavigate } from "react-router-dom"

interface BackButtonProps {
  to: string
  label?: string
  style?: React.CSSProperties
}

export function BackButton({ to, label = "返回", style }: BackButtonProps) {
  const navigate = useNavigate()
  return (
    <button
      type="button"
      onClick={() => navigate(to)}
      style={{
        display: "inline-flex",
        alignItems: "center",
        alignSelf: "flex-start",
        gap: "0.4rem",
        padding: "0.4rem 0.8rem",
        border: "1px solid var(--wj-border-default)",
        borderRadius: "var(--wj-radius-sm)",
        background: "var(--wj-bg-surface)",
        color: "var(--wj-text-secondary)",
        fontSize: "0.85rem",
        fontWeight: 500,
        cursor: "pointer",
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      <ArrowLeft size={15} />
      {label}
    </button>
  )
}
