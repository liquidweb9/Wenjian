import React from "react"
import type { GapType } from "@/lib/types/claim-gap"

interface GapBadgeProps {
  gapType: GapType
}

export function GapBadge({ gapType }: GapBadgeProps) {
  const config = getGapConfig(gapType)

  return (
    <span style={{ ...styles.badge, backgroundColor: config.bgColor, color: config.color }}>
      {config.icon} {config.label}
    </span>
  )
}

function getGapConfig(gapType: GapType) {
  const configs: Record<
    GapType,
    { label: string; icon: string; color: string; bgColor: string }
  > = {
    SUPPORTED_CLAIM: {
      label: "已验证",
      icon: "✓",
      color: "#065f46",
      bgColor: "#d1fae5",
    },
    WEAK_EVIDENCE_CLAIM: {
      label: "证据薄弱",
      icon: "⚠",
      color: "#92400e",
      bgColor: "#fef3c7",
    },
    HIGH_PRIORITY_WEAK_EVIDENCE: {
      label: "高优先级薄弱",
      icon: "⚠",
      color: "#991b1b",
      bgColor: "#fee2e2",
    },
    UNCOVERED_REQUIREMENT: {
      label: "未覆盖需求",
      icon: "○",
      color: "#1e40af",
      bgColor: "#dbeafe",
    },
    IRRELEVANT_CLAIM: {
      label: "无关声明",
      icon: "·",
      color: "#6b7280",
      bgColor: "#f3f4f6",
    },
  }

  return configs[gapType]
}

const styles: Record<string, React.CSSProperties> = {
  badge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    padding: "4px 12px",
    borderRadius: "6px",
    fontSize: "12px",
    fontWeight: 600,
    whiteSpace: "nowrap",
  },
}
