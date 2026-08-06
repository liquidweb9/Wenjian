import React from "react"
import type { GapAnalysisResult } from "@/lib/types/claim-gap"

interface JDCoverageSectionProps {
  gapData: GapAnalysisResult | null
  interviewId: string
}

/**
 * JD Coverage Section - Phase 2.2
 *
 * Displays job description requirement coverage analysis:
 * - Overall coverage percentage
 * - Covered vs uncovered requirements breakdown
 * - High priority gaps
 * - Weak evidence areas
 */
export function JDCoverageSection({
  gapData,
}: JDCoverageSectionProps) {
  if (!gapData) {
    return (
      <div style={styles.emptyState}>
        <div style={styles.emptyIcon}>📊</div>
        <div style={styles.emptyTitle}>暂无岗位覆盖度数据</div>
        <p style={styles.emptyText}>
          本次面试未关联岗位目标，无法生成覆盖度分析。
          关联岗位目标后可查看简历与岗位要求的匹配情况。
        </p>
      </div>
    )
  }

  const stats = gapData.coverage_stats
  const coveragePercentage = stats.coverage_percentage * 100

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>岗位要求覆盖度</h3>
        <p style={styles.subtitle}>
          分析简历陈述与岗位要求的匹配情况，识别优先补强的能力缺口
        </p>
      </div>

      <div style={styles.statsGrid}>
        <StatCard
          label="覆盖率"
          value={`${Math.round(coveragePercentage)}%`}
          description={`${stats.covered_requirements}/${stats.total_requirements} 项要求已覆盖`}
          status={getCoverageStatus(coveragePercentage)}
        />
        <StatCard
          label="未覆盖要求"
          value={String(stats.uncovered_requirements)}
          description="简历中尚未提及的岗位要求"
          status="warning"
        />
        <StatCard
          label="弱证据项"
          value={String(stats.weak_evidence_count)}
          description="有陈述但证据不充分的能力"
          status="caution"
        />
        <StatCard
          label="高优先级缺口"
          value={String(stats.high_priority_gaps)}
          description="需要优先补强的能力缺口"
          status="info"
        />
      </div>

      {gapData.gaps.length > 0 && (
        <div style={styles.gapList}>
          <div style={styles.gapListHeader}>
            <span style={styles.gapListTitle}>关键能力缺口</span>
            <span style={styles.gapListCount}>
              共 {gapData.gaps.length} 项
            </span>
          </div>
          {gapData.gaps.slice(0, 5).map((gap, idx) => (
            <div
              key={`${gap.gap_type}_${gap.requirement_id ?? ""}_${gap.claim_id ?? ""}_${idx}`}
              style={styles.gapCard}
            >
              <div style={styles.gapHeader}>
                <span
                  style={{
                    ...styles.gapType,
                    ...getGapTypeStyle(gap.gap_type),
                  }}
                >
                  {formatGapType(gap.gap_type)}
                </span>
                <span style={styles.gapPriority}>
                  优先级: {Math.round(gap.priority * 100)}
                </span>
              </div>
              <div style={styles.gapCompetency}>{gap.competency_code}</div>
              <div style={styles.gapExplanation}>{gap.explanation}</div>
              {gap.requirement_title && (
                <div style={styles.gapRequirement}>
                  需求: {gap.requirement_title}
                </div>
              )}
            </div>
          ))}
          {gapData.gaps.length > 5 && (
            <div style={styles.moreGaps}>
              还有 {gapData.gaps.length - 5} 项缺口...
            </div>
          )}
        </div>
      )}

      <div style={styles.infoBox}>
        <div style={styles.infoTitle}>💡 关于覆盖度分析</div>
        <p style={styles.infoText}>
          覆盖度分析帮助你了解简历与目标岗位的匹配程度。高优先级缺口会在面试中优先考察，
          弱证据项需要通过深入提问来验证真实能力。
        </p>
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  description,
  status,
}: {
  label: string
  value: string
  description: string
  status: "success" | "warning" | "caution" | "info"
}) {
  return (
    <div style={styles.statCard}>
      <div style={styles.statLabel}>{label}</div>
      <div
        style={{
          ...styles.statValue,
          color: getStatusColor(status),
        }}
      >
        {value}
      </div>
      <div style={styles.statDescription}>{description}</div>
    </div>
  )
}

function getCoverageStatus(
  percentage: number
): "success" | "warning" | "caution" | "info" {
  if (percentage >= 80) return "success"
  if (percentage >= 60) return "info"
  if (percentage >= 40) return "caution"
  return "warning"
}

function getStatusColor(status: string): string {
  const colorMap: Record<string, string> = {
    success: "#16a34a",
    warning: "#dc2626",
    caution: "#ea580c",
    info: "#2563eb",
  }
  return colorMap[status] || "#64748b"
}

function formatGapType(type: string): string {
  const typeMap: Record<string, string> = {
    UNCOVERED_REQUIREMENT: "未覆盖要求",
    HIGH_PRIORITY_WEAK_EVIDENCE: "高优先级薄弱",
    WEAK_EVIDENCE_CLAIM: "证据薄弱",
    IRRELEVANT_CLAIM: "无关声明",
    SUPPORTED_CLAIM: "已支持陈述",
  }
  return typeMap[type] || type
}

function getGapTypeStyle(type: string): React.CSSProperties {
  const styleMap: Record<string, React.CSSProperties> = {
    UNCOVERED_REQUIREMENT: {
      backgroundColor: "#fef2f2",
      color: "#dc2626",
    },
    HIGH_PRIORITY_WEAK_EVIDENCE: {
      backgroundColor: "#fff7ed",
      color: "#ea580c",
    },
    WEAK_EVIDENCE_CLAIM: {
      backgroundColor: "#fff7ed",
      color: "#ea580c",
    },
    IRRELEVANT_CLAIM: {
      backgroundColor: "#f1f5f9",
      color: "#64748b",
    },
    SUPPORTED_CLAIM: {
      backgroundColor: "#f0fdf4",
      color: "#16a34a",
    },
  }
  const fallback: React.CSSProperties = {
    backgroundColor: "#f1f5f9",
    color: "#64748b",
  }
  return (styleMap[type] ?? fallback) as React.CSSProperties
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "grid",
    gap: "1.25rem",
  },
  emptyState: {
    padding: "2.5rem 1.5rem",
    textAlign: "center",
    backgroundColor: "var(--wj-bg-subtle)",
    borderRadius: "0.75rem",
  },
  emptyIcon: {
    fontSize: "3rem",
    marginBottom: "0.75rem",
  },
  emptyTitle: {
    fontSize: "1.1rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
    marginBottom: "0.5rem",
  },
  emptyText: {
    margin: "0.5rem auto 0",
    fontSize: "0.88rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.7,
    maxWidth: 500,
  },
  header: {
    display: "grid",
    gap: "0.5rem",
  },
  title: {
    margin: 0,
    fontSize: "1.2rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
  },
  subtitle: {
    margin: 0,
    fontSize: "0.88rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.6,
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "1rem",
  },
  statCard: {
    padding: "1.25rem",
    backgroundColor: "var(--wj-bg-subtle)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.75rem",
    display: "grid",
    gap: "0.5rem",
  },
  statLabel: {
    fontSize: "0.8rem",
    fontWeight: 600,
    color: "var(--wj-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  statValue: {
    fontSize: "2rem",
    fontWeight: 700,
  },
  statDescription: {
    fontSize: "0.82rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.5,
  },
  gapList: {
    display: "grid",
    gap: "0.75rem",
  },
  gapListHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    paddingBottom: "0.5rem",
    borderBottom: "1px solid var(--wj-border-subtle)",
  },
  gapListTitle: {
    fontSize: "0.9rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
  },
  gapListCount: {
    fontSize: "0.8rem",
    color: "var(--wj-text-secondary)",
  },
  gapCard: {
    padding: "1rem",
    backgroundColor: "var(--wj-bg-subtle)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.5rem",
    display: "grid",
    gap: "0.5rem",
  },
  gapHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "1rem",
  },
  gapType: {
    padding: "0.2rem 0.6rem",
    borderRadius: 999,
    fontSize: "0.75rem",
    fontWeight: 600,
  },
  gapPriority: {
    fontSize: "0.8rem",
    color: "var(--wj-text-secondary)",
  },
  gapCompetency: {
    fontSize: "0.9rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
    fontFamily: '"JetBrains Mono", Consolas, monospace',
  },
  gapExplanation: {
    fontSize: "0.88rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.6,
  },
  gapRequirement: {
    fontSize: "0.82rem",
    color: "var(--wj-text-tertiary)",
    paddingTop: "0.25rem",
    borderTop: "1px solid var(--wj-border-subtle)",
  },
  moreGaps: {
    textAlign: "center",
    padding: "0.75rem",
    fontSize: "0.85rem",
    color: "var(--wj-text-secondary)",
    fontStyle: "italic",
  },
  infoBox: {
    padding: "1rem 1.25rem",
    backgroundColor: "var(--wj-info-bg)",
    border: "1px solid rgba(37, 99, 235, 0.2)",
    borderRadius: "0.75rem",
  },
  infoTitle: {
    margin: 0,
    marginBottom: "0.5rem",
    fontSize: "0.9rem",
    fontWeight: 600,
    color: "var(--wj-info)",
  },
  infoText: {
    margin: 0,
    fontSize: "0.85rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.7,
  },
}
