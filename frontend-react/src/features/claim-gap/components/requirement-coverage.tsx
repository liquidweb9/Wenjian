import React from "react"
import type { ClaimGap, GapAnalysisResult } from "@/lib/types/claim-gap"
import { GapBadge } from "./gap-badge"

interface RequirementCoverageProps {
  analysis: GapAnalysisResult
}

const MAX_LEVEL = 5

export function RequirementCoverage({ analysis }: RequirementCoverageProps) {
  const { gaps } = analysis

  // Each gap links a claim to a requirement; group by requirement to show coverage.
  // UNCOVERED_REQUIREMENT gaps have no claim mapping and are rendered separately below.
  const requirementMap = new Map<string, ClaimGap[]>()

  gaps.forEach((gap) => {
    if (!gap.requirement_id) return
    if (gap.gap_type === "UNCOVERED_REQUIREMENT") return
    const existing = requirementMap.get(gap.requirement_id) || []
    requirementMap.set(gap.requirement_id, [...existing, gap])
  })

  // Uncovered requirements have no claim mapping.
  const uncoveredRequirements = gaps.filter(
    (gap) => gap.gap_type === "UNCOVERED_REQUIREMENT"
  )

  const sortedRequirementIds = Array.from(requirementMap.keys()).sort((a, b) => {
    const mappingsA = requirementMap.get(a) || []
    const mappingsB = requirementMap.get(b) || []
    const avgCoverageA = avgClaimCoverage(mappingsA)
    const avgCoverageB = avgClaimCoverage(mappingsB)
    return avgCoverageB - avgCoverageA
  })

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>需求覆盖详情</h2>
        <p style={styles.subtitle}>
          展示每个岗位需求的 Claim 覆盖情况，帮助识别未覆盖或覆盖不足的能力要求
        </p>
      </div>

      {/* Covered Requirements */}
      {sortedRequirementIds.length > 0 && (
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>
            已覆盖需求 ({sortedRequirementIds.length})
          </h3>
          <div style={styles.requirementList}>
            {sortedRequirementIds.map((requirementId) => {
              const mappings = requirementMap.get(requirementId) || []
              const avgCoverage = avgClaimCoverage(mappings)
              const title = mappings.find((m) => m.requirement_title)?.requirement_title

              return (
                <div key={requirementId} style={styles.requirementCard}>
                  <div style={styles.requirementHeader}>
                    <div style={styles.requirementIdBadge}>{requirementId}</div>
                    {title && <div style={styles.requirementTitle}>{title}</div>}
                    <div style={styles.coverageBar}>
                      <div
                        style={{
                          ...styles.coverageFill,
                          width: `${avgCoverage}%`,
                          backgroundColor: getCoverageColor(avgCoverage),
                        }}
                      />
                      <span style={styles.coverageText}>{Math.round(avgCoverage)}% 覆盖</span>
                    </div>
                  </div>

                  <div style={styles.claimMappings}>
                    {mappings.map((mapping, idx) => (
                      <div key={idx} style={styles.mappingRow}>
                        <div style={styles.mappingLeft}>
                          <span style={styles.claimId}>{mapping.claim_id || "—"}</span>
                          <GapBadge gapType={mapping.gap_type} />
                        </div>
                        <div style={styles.mappingRight}>
                          <div
                            style={{
                              ...styles.scoreBar,
                              width: `${coveragePercent(mapping.claim_coverage_level)}%`,
                              backgroundColor: getCoverageColor(coveragePercent(mapping.claim_coverage_level)),
                            }}
                          />
                          <span style={styles.scoreText}>
                            {Math.round(coveragePercent(mapping.claim_coverage_level))}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {mappings[0]?.explanation && (
                    <div style={styles.reasoning}>
                      <span style={styles.reasoningLabel}>分析:</span>
                      <span style={styles.reasoningText}>{mappings[0].explanation}</span>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Uncovered Requirements */}
      {uncoveredRequirements.length > 0 && (
        <div style={styles.section}>
          <h3 style={{ ...styles.sectionTitle, color: "#dc2626" }}>
            未覆盖需求 ({uncoveredRequirements.length})
          </h3>
          <div style={styles.requirementList}>
            {uncoveredRequirements.map((gap, idx) => (
              <div key={gap.requirement_id || idx} style={styles.uncoveredCard}>
                <div style={styles.uncoveredHeader}>
                  <div style={styles.uncoveredTitle}>
                    {gap.requirement_title || gap.requirement_id || "未命名需求"}
                  </div>
                  <div style={styles.competencyBadge}>{gap.competency_code}</div>
                </div>
                <p style={styles.uncoveredDescription}>{gap.explanation}</p>
                <div style={styles.uncoveredMeta}>
                  <span style={styles.metaItem}>
                    重要度: {(gap.requirement_importance ?? 0).toFixed(2)}
                  </span>
                  <span style={styles.metaItem}>
                    期望级别: {gap.requirement_expected_level ?? "—"} / {MAX_LEVEL}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {sortedRequirementIds.length === 0 && uncoveredRequirements.length === 0 && (
        <div style={styles.emptyState}>
          <p style={styles.emptyText}>暂无需求映射数据</p>
        </div>
      )}
    </div>
  )
}

function avgClaimCoverage(mappings: ClaimGap[]): number {
  if (mappings.length === 0) return 0
  const sum = mappings.reduce((acc, m) => acc + coveragePercent(m.claim_coverage_level), 0)
  return sum / mappings.length
}

function coveragePercent(level: number | null): number {
  if (level == null) return 0
  return Math.min(100, (level / MAX_LEVEL) * 100)
}

function getCoverageColor(coverage: number): string {
  if (coverage >= 80) return "#059669" // Green
  if (coverage >= 60) return "#d97706" // Orange
  if (coverage >= 40) return "#dc2626" // Red
  return "#9ca3af" // Gray
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
    margin: "0 0 8px 0",
  },
  subtitle: {
    fontSize: "13px",
    color: "#6b7280",
    margin: 0,
    lineHeight: 1.5,
  },
  section: {
    marginBottom: "32px",
  },
  sectionTitle: {
    fontSize: "16px",
    fontWeight: 600,
    color: "#1a1a1a",
    margin: "0 0 16px 0",
  },
  requirementList: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  requirementCard: {
    padding: "16px",
    backgroundColor: "#f9fafb",
    borderRadius: "8px",
    border: "1px solid #e5e7eb",
  },
  requirementHeader: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "12px",
  },
  requirementIdBadge: {
    fontSize: "11px",
    fontWeight: 700,
    color: "#1e40af",
    backgroundColor: "#dbeafe",
    padding: "4px 10px",
    borderRadius: "4px",
    border: "1px solid #93c5fd",
    flexShrink: 0,
  },
  requirementTitle: {
    fontSize: "13px",
    fontWeight: 600,
    color: "#374151",
    flexShrink: 0,
  },
  coverageBar: {
    flex: 1,
    height: "24px",
    backgroundColor: "#e5e7eb",
    borderRadius: "6px",
    position: "relative",
    overflow: "hidden",
  },
  coverageFill: {
    height: "100%",
    transition: "width 0.4s ease",
    borderRadius: "6px",
  },
  coverageText: {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    fontSize: "11px",
    fontWeight: 700,
    color: "#1a1a1a",
    textShadow: "0 0 3px rgba(255,255,255,0.8)",
  },
  claimMappings: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    marginBottom: "12px",
  },
  mappingRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "8px 12px",
    backgroundColor: "#ffffff",
    borderRadius: "6px",
  },
  mappingLeft: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  claimId: {
    fontSize: "12px",
    fontWeight: 600,
    color: "#4b5563",
  },
  mappingRight: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  scoreBar: {
    width: "60px",
    height: "6px",
    borderRadius: "3px",
    transition: "width 0.3s ease",
  },
  scoreText: {
    fontSize: "11px",
    fontWeight: 700,
    color: "#6b7280",
    width: "25px",
    textAlign: "right",
  },
  reasoning: {
    padding: "10px 12px",
    backgroundColor: "#ffffff",
    borderRadius: "6px",
    fontSize: "12px",
    color: "#4b5563",
    lineHeight: 1.5,
  },
  reasoningLabel: {
    fontWeight: 600,
    color: "#6b7280",
    marginRight: "6px",
  },
  reasoningText: {
    color: "#4b5563",
  },
  uncoveredCard: {
    padding: "16px",
    backgroundColor: "#fef2f2",
    borderRadius: "8px",
    border: "1px solid #fecaca",
  },
  uncoveredHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "8px",
  },
  uncoveredTitle: {
    fontSize: "14px",
    fontWeight: 600,
    color: "#991b1b",
  },
  competencyBadge: {
    fontSize: "11px",
    fontWeight: 700,
    color: "#7c2d12",
    backgroundColor: "#fed7aa",
    padding: "3px 8px",
    borderRadius: "4px",
  },
  uncoveredDescription: {
    fontSize: "13px",
    color: "#7f1d1d",
    margin: "0 0 10px 0",
    lineHeight: 1.5,
  },
  uncoveredMeta: {
    display: "flex",
    gap: "12px",
  },
  metaItem: {
    fontSize: "12px",
    color: "#7f1d1d",
    backgroundColor: "#fff7ed",
    padding: "4px 10px",
    borderRadius: "4px",
    border: "1px solid #fed7aa",
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
}
