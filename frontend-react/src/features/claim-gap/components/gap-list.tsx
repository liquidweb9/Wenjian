import React, { useState } from "react"
import type { ClaimGap, GapType } from "@/lib/types/claim-gap"
import { GapBadge } from "./gap-badge"

interface GapListProps {
  gaps: ClaimGap[]
}

const MAX_LEVEL = 5

export function GapList({ gaps }: GapListProps) {
  const [selectedType, setSelectedType] = useState<GapType | "ALL">("ALL")

  const filteredGaps =
    selectedType === "ALL" ? gaps : gaps.filter((gap) => gap.gap_type === selectedType)

  const sortedGaps = [...filteredGaps].sort((a, b) => b.priority - a.priority)

  const gapCounts = gaps.reduce(
    (acc, gap) => {
      acc[gap.gap_type] = (acc[gap.gap_type] || 0) + 1
      return acc
    },
    {} as Record<GapType, number>
  )

  const filterOptions: Array<{ value: GapType | "ALL"; label: string }> = [
    { value: "ALL", label: `全部 (${gaps.length})` },
    {
      value: "UNCOVERED_REQUIREMENT",
      label: `未覆盖 (${gapCounts.UNCOVERED_REQUIREMENT || 0})`,
    },
    {
      value: "HIGH_PRIORITY_WEAK_EVIDENCE",
      label: `高优先级薄弱 (${gapCounts.HIGH_PRIORITY_WEAK_EVIDENCE || 0})`,
    },
    {
      value: "WEAK_EVIDENCE_CLAIM",
      label: `证据薄弱 (${gapCounts.WEAK_EVIDENCE_CLAIM || 0})`,
    },
    {
      value: "IRRELEVANT_CLAIM",
      label: `无关声明 (${gapCounts.IRRELEVANT_CLAIM || 0})`,
    },
    { value: "SUPPORTED_CLAIM", label: `已验证 (${gapCounts.SUPPORTED_CLAIM || 0})` },
  ]

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>能力缺口明细</h2>
        <div style={styles.filters}>
          {filterOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setSelectedType(option.value)}
              style={{
                ...styles.filterButton,
                ...(selectedType === option.value ? styles.filterButtonActive : {}),
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {sortedGaps.length === 0 ? (
        <div style={styles.emptyState}>
          <p style={styles.emptyText}>没有找到符合条件的缺口项</p>
        </div>
      ) : (
        <div style={styles.gapList}>
          {sortedGaps.map((gap, idx) => (
            <div
              key={`${gap.gap_type}_${gap.requirement_id ?? ""}_${gap.claim_id ?? ""}_${idx}`}
              style={styles.gapCard}
            >
              <div style={styles.gapHeader}>
                <div style={styles.gapTitleRow}>
                  <h3 style={styles.gapTitle}>
                    {gap.requirement_title || gap.claim_text || "缺口项"}
                  </h3>
                  <GapBadge gapType={gap.gap_type} />
                </div>
                <div style={styles.gapMeta}>
                  <span style={styles.metaBadge}>{gap.competency_code}</span>
                  <span style={styles.priorityBadge}>
                    优先级: {Math.round(gap.priority * 100)}
                  </span>
                </div>
              </div>

              <p style={styles.description}>{gap.explanation}</p>

              {gap.claim_text && (
                <div style={styles.claimQuote}>
                  <span style={styles.claimLabel}>相关声明:</span>
                  <span style={styles.claimText}>{gap.claim_text}</span>
                </div>
              )}

              {gap.reason_codes.length > 0 && (
                <div style={styles.reasonCodes}>
                  <span style={styles.reasonLabel}>原因:</span>
                  <div style={styles.reasonList}>
                    {gap.reason_codes.map((code, i) => (
                      <span key={i} style={styles.reasonCode}>
                        {code}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div style={styles.detailBox}>
                <div style={styles.detailLabel}>需求详情:</div>
                <div style={styles.detailRow}>
                  <span style={styles.detailItem}>
                    重要度: {(gap.requirement_importance ?? 0).toFixed(2)}
                  </span>
                  <span style={styles.detailItem}>
                    期望级别: {gap.requirement_expected_level ?? "—"} / {MAX_LEVEL}
                  </span>
                  <span style={styles.detailItem}>
                    当前覆盖: {gap.claim_coverage_level ?? "—"} / {MAX_LEVEL}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: "#ffffff",
    borderRadius: "12px",
    border: "1px solid #e5e7eb",
    padding: "24px",
  },
  header: {
    marginBottom: "24px",
  },
  title: {
    fontSize: "20px",
    fontWeight: 600,
    color: "#1a1a1a",
    margin: "0 0 16px 0",
  },
  filters: {
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
  },
  filterButton: {
    padding: "6px 14px",
    fontSize: "13px",
    fontWeight: 500,
    color: "#6b7280",
    backgroundColor: "#f9fafb",
    border: "1px solid #e5e7eb",
    borderRadius: "6px",
    cursor: "pointer",
    transition: "all 0.2s",
  },
  filterButtonActive: {
    color: "#1a1a1a",
    backgroundColor: "#e5e7eb",
    borderColor: "#9ca3af",
  },
  emptyState: {
    padding: "48px 24px",
    textAlign: "center",
  },
  emptyText: {
    fontSize: "14px",
    color: "#9ca3af",
    margin: 0,
  },
  gapList: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  gapCard: {
    padding: "20px",
    backgroundColor: "#f9fafb",
    borderRadius: "8px",
    border: "1px solid #e5e7eb",
  },
  gapHeader: {
    marginBottom: "12px",
  },
  gapTitleRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "8px",
  },
  gapTitle: {
    fontSize: "16px",
    fontWeight: 600,
    color: "#1a1a1a",
    margin: 0,
  },
  gapMeta: {
    display: "flex",
    gap: "8px",
    alignItems: "center",
  },
  metaBadge: {
    fontSize: "11px",
    fontWeight: 600,
    color: "#6b7280",
    backgroundColor: "#ffffff",
    padding: "3px 8px",
    borderRadius: "4px",
    border: "1px solid #e5e7eb",
  },
  priorityBadge: {
    fontSize: "11px",
    fontWeight: 600,
    color: "#7c3aed",
    backgroundColor: "#f5f3ff",
    padding: "3px 8px",
    borderRadius: "4px",
  },
  description: {
    fontSize: "14px",
    color: "#4b5563",
    lineHeight: 1.6,
    margin: "0 0 12px 0",
  },
  claimQuote: {
    padding: "10px 12px",
    backgroundColor: "#f5f3ff",
    borderRadius: "6px",
    marginBottom: "12px",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  claimLabel: {
    fontSize: "12px",
    fontWeight: 600,
    color: "#5b21b6",
  },
  claimText: {
    fontSize: "13px",
    color: "#4c1d95",
    lineHeight: 1.5,
  },
  reasonCodes: {
    marginBottom: "12px",
  },
  reasonLabel: {
    fontSize: "12px",
    fontWeight: 600,
    color: "#6b7280",
    marginBottom: "6px",
    display: "block",
  },
  reasonList: {
    display: "flex",
    gap: "6px",
    flexWrap: "wrap",
  },
  reasonCode: {
    fontSize: "11px",
    color: "#3b82f6",
    backgroundColor: "#eff6ff",
    padding: "3px 8px",
    borderRadius: "4px",
    border: "1px solid #bfdbfe",
  },
  detailBox: {
    padding: "12px",
    backgroundColor: "#ffffff",
    borderRadius: "6px",
    border: "1px solid #e5e7eb",
  },
  detailLabel: {
    fontSize: "12px",
    fontWeight: 600,
    color: "#6b7280",
    marginBottom: "6px",
  },
  detailRow: {
    display: "flex",
    gap: "12px",
    flexWrap: "wrap",
  },
  detailItem: {
    fontSize: "12px",
    color: "#374151",
    backgroundColor: "#f9fafb",
    padding: "3px 8px",
    borderRadius: "4px",
    border: "1px solid #e5e7eb",
  },
}
