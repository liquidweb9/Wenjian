import React from "react"
import type { Contradiction } from "../api/evidence-api"
import type { VerificationPoint } from "../api/evidence-api"

interface UnresolvedIssuesSectionProps {
  contradictions: Contradiction[]
  weakVerificationPoints: VerificationPoint[]
  interviewId: string
}

/**
 * Unresolved Issues Section - Phase 2.2
 *
 * Displays unresolved contradictions and weak evidence that require attention:
 * - Contradictions detected between resume claims and interview answers
 * - Verification points with weak or insufficient evidence
 * - Suggested follow-up actions
 */
export function UnresolvedIssuesSection({
  contradictions,
  weakVerificationPoints,
}: UnresolvedIssuesSectionProps) {
  const hasIssues = contradictions.length > 0 || weakVerificationPoints.length > 0

  if (!hasIssues) {
    return (
      <div style={styles.emptyState}>
        <div style={styles.emptyIcon}>✓</div>
        <div style={styles.emptyTitle}>未发现待解决问题</div>
        <p style={styles.emptyText}>
          本次面试中所有陈述均已得到充分验证，未检测到矛盾或证据不足的情况。
        </p>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>待解决问题</h3>
        <p style={styles.subtitle}>
          需要进一步澄清的矛盾和证据不足的验证点
        </p>
      </div>

      {contradictions.length > 0 && (
        <div style={styles.section}>
          <div style={styles.sectionHeader}>
            <span style={styles.sectionIcon}>⚠️</span>
            <span style={styles.sectionTitle}>
              矛盾检测 ({contradictions.length})
            </span>
          </div>
          <div style={styles.issueList}>
            {contradictions.map((contradiction, index) => (
              <div key={contradiction.contradiction_id} style={styles.issueCard}>
                <div style={styles.issueHeader}>
                  <span style={styles.issueIndex}>矛盾 #{index + 1}</span>
                  <span
                    style={{
                      ...styles.severityBadge,
                      ...getSeverityStyle(contradiction.severity),
                    }}
                  >
                    {formatSeverity(contradiction.severity)}
                  </span>
                </div>

                <div style={styles.issueContent}>
                  <div style={styles.issueLabel}>简历陈述</div>
                  <div style={styles.issueText}>
                    Claim ID: {contradiction.claim_id}
                  </div>
                </div>

                <div style={styles.issueContent}>
                  <div style={styles.issueLabel}>矛盾描述</div>
                  <div style={styles.issueText}>{contradiction.description}</div>
                </div>

                {contradiction.conflicting_answers && contradiction.conflicting_answers.length > 0 && (
                  <div style={styles.issueContent}>
                    <div style={styles.issueLabel}>冲突回答</div>
                    {contradiction.conflicting_answers.map((answer, idx) => (
                      <div key={idx} style={styles.issueText}>
                        {answer.text}
                      </div>
                    ))}
                  </div>
                )}

                {contradiction.clarification_question && (
                  <div style={styles.clarificationBox}>
                    <span style={styles.clarificationIcon}>💡</span>
                    <span style={styles.clarificationText}>
                      建议澄清: {contradiction.clarification_question}
                    </span>
                  </div>
                )}

                <div style={styles.issueFooter}>
                  <span style={styles.issueMetaItem}>
                    验证点: {contradiction.verification_point_id.slice(0, 8)}...
                  </span>
                  <span style={styles.issueStatus}>
                    {contradiction.resolution_status === "RESOLVED" ? "已解决" : "待澄清"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {weakVerificationPoints.length > 0 && (
        <div style={styles.section}>
          <div style={styles.sectionHeader}>
            <span style={styles.sectionIcon}>⚡</span>
            <span style={styles.sectionTitle}>
              弱证据验证点 ({weakVerificationPoints.length})
            </span>
          </div>
          <div style={styles.issueList}>
            {weakVerificationPoints.map((vp, index) => (
              <div key={vp.verification_point_id} style={styles.issueCard}>
                <div style={styles.issueHeader}>
                  <span style={styles.issueIndex}>验证点 #{index + 1}</span>
                  <span
                    style={{
                      ...styles.stateBadge,
                      ...getStateStyle(vp.current_state),
                    }}
                  >
                    {formatState(vp.current_state)}
                  </span>
                </div>

                <div style={styles.issueContent}>
                  <div style={styles.issueLabel}>验证维度</div>
                  <div style={styles.issueText}>{vp.aspect}</div>
                </div>

                <div style={styles.issueContent}>
                  <div style={styles.issueLabel}>能力代码</div>
                  <div style={styles.competencyCode}>{vp.competency_code}</div>
                </div>

                <div style={styles.strengthBar}>
                  <div style={styles.strengthLabel}>
                    证据强度: {vp.strength !== null ? Math.round(vp.strength * 100) : 0}%
                  </div>
                  <div style={styles.strengthBarBg}>
                    <div
                      style={{
                        ...styles.strengthBarFill,
                        width: `${vp.strength !== null ? vp.strength * 100 : 0}%`,
                        backgroundColor: getStrengthColor(vp.strength ?? 0),
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={styles.infoBox}>
        <div style={styles.infoTitle}>💡 关于待解决问题</div>
        <p style={styles.infoText}>
          矛盾检测帮助发现简历陈述与实际回答不一致的地方，需要进一步澄清。
          弱证据验证点表示虽然涉及了相关话题，但回答深度或具体性不足以充分验证能力。
          建议在后续面试中针对这些问题进行深入追问。
        </p>
      </div>
    </div>
  )
}

function formatSeverity(severity: string): string {
  const severityMap: Record<string, string> = {
    HIGH: "高",
    MEDIUM: "中",
    LOW: "低",
  }
  return severityMap[severity] || severity
}

function getSeverityStyle(severity: string): React.CSSProperties {
  const styleMap: Record<string, React.CSSProperties> = {
    HIGH: {
      backgroundColor: "#fef2f2",
      color: "#dc2626",
    },
    MEDIUM: {
      backgroundColor: "#fff7ed",
      color: "#ea580c",
    },
    LOW: {
      backgroundColor: "#fef9c3",
      color: "#ca8a04",
    },
  }
  return (
    styleMap[severity] || {
      backgroundColor: "#f1f5f9",
      color: "#64748b",
    }
  )
}

function formatState(state: string): string {
  const stateMap: Record<string, string> = {
    UNSEEN: "未涉及",
    ADDRESSED: "已涉及",
    PARTIALLY_SUPPORTED: "部分支持",
    VERIFIED: "已验证",
    CONTRADICTORY: "矛盾",
  }
  return stateMap[state] || state
}

function getStateStyle(state: string): React.CSSProperties {
  const stateStyles: Record<string, React.CSSProperties> = {
    PARTIALLY_SUPPORTED: {
      backgroundColor: "#fff7ed",
      color: "#ea580c",
    },
    ADDRESSED: {
      backgroundColor: "#eff6ff",
      color: "#2563eb",
    },
    UNSEEN: {
      backgroundColor: "#f1f5f9",
      color: "#94a3b8",
    },
  }
  return (
    stateStyles[state] || {
      backgroundColor: "#f1f5f9",
      color: "#64748b",
    }
  )
}

function getStrengthColor(strength: number): string {
  if (strength >= 0.8) return "#16a34a"
  if (strength >= 0.6) return "#2563eb"
  if (strength >= 0.4) return "#ea580c"
  return "#dc2626"
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "grid",
    gap: "1.25rem",
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
  emptyState: {
    padding: "2.5rem 1.5rem",
    textAlign: "center",
    backgroundColor: "var(--wj-bg-subtle)",
    borderRadius: "0.75rem",
  },
  emptyIcon: {
    fontSize: "3rem",
    marginBottom: "0.75rem",
    color: "var(--wj-success)",
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
  section: {
    display: "grid",
    gap: "1rem",
  },
  sectionHeader: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    paddingBottom: "0.5rem",
    borderBottom: "2px solid var(--wj-border-default)",
  },
  sectionIcon: {
    fontSize: "1.2rem",
  },
  sectionTitle: {
    fontSize: "1rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
  },
  issueList: {
    display: "grid",
    gap: "0.75rem",
  },
  issueCard: {
    padding: "1.25rem",
    backgroundColor: "var(--wj-bg-subtle)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.75rem",
    display: "grid",
    gap: "1rem",
  },
  issueHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "1rem",
  },
  issueIndex: {
    fontSize: "0.85rem",
    fontWeight: 600,
    color: "var(--wj-brand-primary)",
  },
  severityBadge: {
    padding: "0.2rem 0.6rem",
    borderRadius: 999,
    fontSize: "0.75rem",
    fontWeight: 600,
  },
  stateBadge: {
    padding: "0.2rem 0.6rem",
    borderRadius: 999,
    fontSize: "0.75rem",
    fontWeight: 600,
  },
  issueContent: {
    display: "grid",
    gap: "0.35rem",
  },
  issueLabel: {
    fontSize: "0.75rem",
    fontWeight: 600,
    color: "var(--wj-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  issueText: {
    fontSize: "0.9rem",
    color: "var(--wj-text-primary)",
    lineHeight: 1.7,
  },
  issueExplanation: {
    fontSize: "0.88rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.7,
    fontStyle: "italic",
  },
  competencyCode: {
    fontSize: "0.9rem",
    fontWeight: 500,
    color: "var(--wj-text-primary)",
    fontFamily: '"JetBrains Mono", Consolas, monospace',
  },
  clarificationBox: {
    display: "flex",
    gap: "0.5rem",
    padding: "0.75rem 1rem",
    backgroundColor: "var(--wj-info-bg)",
    border: "1px solid rgba(37, 99, 235, 0.2)",
    borderRadius: "0.5rem",
  },
  clarificationIcon: {
    fontSize: "1rem",
    flexShrink: 0,
  },
  clarificationText: {
    fontSize: "0.85rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.6,
  },
  issueFooter: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "1rem",
    paddingTop: "0.75rem",
    borderTop: "1px solid var(--wj-border-subtle)",
    fontSize: "0.8rem",
  },
  issueMetaItem: {
    color: "var(--wj-text-tertiary)",
    fontFamily: '"JetBrains Mono", Consolas, monospace',
  },
  issueStatus: {
    color: "var(--wj-text-secondary)",
    fontWeight: 500,
  },
  strengthBar: {
    display: "grid",
    gap: "0.35rem",
  },
  strengthLabel: {
    fontSize: "0.8rem",
    color: "var(--wj-text-secondary)",
  },
  strengthBarBg: {
    height: 8,
    backgroundColor: "var(--wj-bg-surface)",
    borderRadius: 999,
    overflow: "hidden",
  },
  strengthBarFill: {
    height: "100%",
    borderRadius: 999,
    transition: "width 0.3s ease",
  },
  reasonCodes: {
    display: "grid",
    gap: "0.5rem",
  },
  reasonCodesLabel: {
    fontSize: "0.8rem",
    fontWeight: 600,
    color: "var(--wj-text-secondary)",
  },
  reasonCodesList: {
    display: "flex",
    flexWrap: "wrap",
    gap: "0.5rem",
  },
  reasonCode: {
    padding: "0.25rem 0.6rem",
    backgroundColor: "var(--wj-bg-surface)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.375rem",
    fontSize: "0.75rem",
    color: "var(--wj-text-secondary)",
    fontFamily: '"JetBrains Mono", Consolas, monospace',
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
