import React from "react"
import { Link } from "react-router-dom"
import type { Evidence } from "../api/evidence-api"

interface EvidenceSpanViewerProps {
  verificationPointId: string
  aspect: string
  currentState: string
  evidence: Evidence[]
  interviewId: string
}

/**
 * Evidence Span Viewer - Phase 2.2
 *
 * Displays evidence spans extracted from interview answers with:
 * - Highlighted text spans showing what was extracted
 * - Evidence type and confidence
 * - Links to the specific Q&A where evidence was found
 * - Extraction metadata (prompt version, timestamp)
 */
export function EvidenceSpanViewer({
  aspect,
  currentState,
  evidence,
  interviewId,
}: EvidenceSpanViewerProps) {
  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>证据片段</h3>
        <div style={styles.meta}>
          <span style={styles.metaLabel}>验证点:</span>
          <span style={styles.metaValue}>{aspect}</span>
        </div>
        <div style={styles.meta}>
          <span style={styles.metaLabel}>当前状态:</span>
          <span style={{
            ...styles.statusPill,
            ...getStateStyle(currentState),
          }}>
            {currentState}
          </span>
        </div>
      </div>

      {evidence.length === 0 ? (
        <div style={styles.emptyState}>
          <p style={styles.emptyText}>暂无证据片段</p>
          <p style={styles.emptyHint}>
            系统尚未从面试回答中提取到支持此验证点的证据。
          </p>
        </div>
      ) : (
        <div style={styles.evidenceList}>
          {evidence.map((ev, index) => (
            <div key={ev.evidence_id} style={styles.evidenceCard}>
              <div style={styles.evidenceHeader}>
                <div style={styles.evidenceIndex}>证据 #{index + 1}</div>
                <div style={styles.evidenceMeta}>
                  <span style={{
                    ...styles.typeBadge,
                    ...getTypeBadgeStyle(ev.evidence_type),
                  }}>
                    {formatEvidenceType(ev.evidence_type)}
                  </span>
                  <span style={styles.confidence}>
                    置信度: {Math.round(ev.confidence * 100)}%
                  </span>
                </div>
              </div>

              {ev.summary && (
                <div style={styles.summary}>
                  <div style={styles.summaryLabel}>证据摘要</div>
                  <p style={styles.summaryText}>{ev.summary}</p>
                </div>
              )}

              {ev.spans && ev.spans.length > 0 && (
                <div style={styles.spans}>
                  <div style={styles.spansLabel}>文本片段</div>
                  {ev.spans.map((span, spanIdx) => (
                    <div key={spanIdx} style={styles.spanItem}>
                      <div style={styles.spanText}>"{span.text}"</div>
                      <div style={styles.spanMeta}>
                        <span style={styles.spanPosition}>
                          位置: {span.start}–{span.end}
                        </span>
                        <span style={styles.spanHash}>
                          校验: {span.quote_hash.slice(0, 8)}...
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div style={styles.footer}>
                <Link
                  to={`/app/interviews/${interviewId}`}
                  style={styles.viewAnswerLink}
                >
                  查看完整问答 →
                </Link>
                <div style={styles.extractionInfo}>
                  <span style={styles.extractionLabel}>提取来源:</span>
                  <span style={styles.extractionValue}>{ev.extracted_by}</span>
                </div>
                <div style={styles.timestamp}>
                  {formatTimestamp(ev.created_at)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={styles.infoBox}>
        <div style={styles.infoTitle}>💡 关于证据片段</div>
        <p style={styles.infoText}>
          证据片段是系统从你的面试回答中提取的关键内容，用于验证简历陈述的真实性。
          每个片段都包含原文位置、校验哈希值（防篡改）和提取置信度。
        </p>
      </div>
    </div>
  )
}

function formatEvidenceType(type: string): string {
  const typeMap: Record<string, string> = {
    DIRECT: "直接证据",
    INDIRECT: "间接证据",
    CONTEXTUAL: "背景证据",
  }
  return typeMap[type] || type
}

function getStateStyle(state: string): React.CSSProperties {
  const stateStyles: Record<string, React.CSSProperties> = {
    VERIFIED: {
      backgroundColor: "#f0fdf4",
      color: "#16a34a",
    },
    PARTIALLY_SUPPORTED: {
      backgroundColor: "#fff7ed",
      color: "#ea580c",
    },
    ADDRESSED: {
      backgroundColor: "#eff6ff",
      color: "#2563eb",
    },
    CONTRADICTORY: {
      backgroundColor: "#fef2f2",
      color: "#dc2626",
    },
    UNSEEN: {
      backgroundColor: "#f1f5f9",
      color: "#94a3b8",
    },
  }
  return (stateStyles[state] ?? stateStyles.UNSEEN) as React.CSSProperties
}

function getTypeBadgeStyle(type: string): React.CSSProperties {
  const typeStyles: Record<string, React.CSSProperties> = {
    DIRECT: {
      backgroundColor: "#dcfce7",
      color: "#16a34a",
    },
    INDIRECT: {
      backgroundColor: "#fef3c7",
      color: "#d97706",
    },
    CONTEXTUAL: {
      backgroundColor: "#dbeafe",
      color: "#2563eb",
    },
  }
  const fallback: React.CSSProperties = { backgroundColor: "#f1f5f9", color: "#64748b" }
  return (typeStyles[type] ?? fallback) as React.CSSProperties
}

function formatTimestamp(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMinutes = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMinutes < 1) return "刚刚"
  if (diffMinutes < 60) return `${diffMinutes} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays < 7) return `${diffDays} 天前`

  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  })
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "grid",
    gap: "1.25rem",
  },
  header: {
    display: "grid",
    gap: "0.75rem",
  },
  title: {
    margin: 0,
    fontSize: "1.2rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
  },
  meta: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    fontSize: "0.85rem",
  },
  metaLabel: {
    color: "var(--wj-text-secondary)",
  },
  metaValue: {
    color: "var(--wj-text-primary)",
    fontWeight: 500,
  },
  statusPill: {
    padding: "0.25rem 0.65rem",
    borderRadius: 999,
    fontSize: "0.75rem",
    fontWeight: 600,
  },
  emptyState: {
    padding: "2rem",
    textAlign: "center",
    backgroundColor: "var(--wj-bg-subtle)",
    borderRadius: "0.75rem",
  },
  emptyText: {
    margin: 0,
    fontSize: "1rem",
    fontWeight: 500,
    color: "var(--wj-text-primary)",
  },
  emptyHint: {
    margin: "0.5rem 0 0",
    fontSize: "0.85rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.6,
  },
  evidenceList: {
    display: "grid",
    gap: "1rem",
  },
  evidenceCard: {
    padding: "1.25rem",
    backgroundColor: "var(--wj-bg-subtle)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.75rem",
    display: "grid",
    gap: "1rem",
  },
  evidenceHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "1rem",
  },
  evidenceIndex: {
    fontSize: "0.85rem",
    fontWeight: 600,
    color: "var(--wj-brand-primary)",
  },
  evidenceMeta: {
    display: "flex",
    alignItems: "center",
    gap: "0.75rem",
  },
  typeBadge: {
    padding: "0.2rem 0.6rem",
    borderRadius: 999,
    fontSize: "0.75rem",
    fontWeight: 600,
  },
  confidence: {
    fontSize: "0.8rem",
    color: "var(--wj-text-secondary)",
  },
  summary: {
    display: "grid",
    gap: "0.5rem",
  },
  summaryLabel: {
    fontSize: "0.8rem",
    fontWeight: 600,
    color: "var(--wj-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  summaryText: {
    margin: 0,
    fontSize: "0.9rem",
    color: "var(--wj-text-primary)",
    lineHeight: 1.7,
  },
  spans: {
    display: "grid",
    gap: "0.75rem",
  },
  spansLabel: {
    fontSize: "0.8rem",
    fontWeight: 600,
    color: "var(--wj-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  spanItem: {
    padding: "0.9rem",
    backgroundColor: "var(--wj-bg-surface)",
    border: "1px solid var(--wj-border-subtle)",
    borderRadius: "0.5rem",
    display: "grid",
    gap: "0.5rem",
  },
  spanText: {
    fontSize: "0.9rem",
    color: "var(--wj-text-primary)",
    lineHeight: 1.7,
    fontStyle: "italic",
  },
  spanMeta: {
    display: "flex",
    gap: "1rem",
    fontSize: "0.75rem",
    color: "var(--wj-text-tertiary)",
  },
  spanPosition: {},
  spanHash: {
    fontFamily: '"JetBrains Mono", Consolas, monospace',
  },
  footer: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "1rem",
    paddingTop: "0.75rem",
    borderTop: "1px solid var(--wj-border-subtle)",
    fontSize: "0.8rem",
  },
  viewAnswerLink: {
    color: "var(--wj-brand-primary)",
    textDecoration: "none",
    fontWeight: 500,
    transition: "color 0.15s",
  },
  extractionInfo: {
    display: "flex",
    gap: "0.5rem",
    color: "var(--wj-text-tertiary)",
  },
  extractionLabel: {},
  extractionValue: {
    fontFamily: '"JetBrains Mono", Consolas, monospace',
  },
  timestamp: {
    color: "var(--wj-text-tertiary)",
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
