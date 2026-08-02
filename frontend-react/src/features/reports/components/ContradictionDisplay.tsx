import React from "react"
import type { Contradiction } from "../api/evidence-api"

interface ContradictionDisplayProps {
  contradictions: Contradiction[]
  onAskClarification?: (contradictionId: string, question: string) => void
  onMarkResolved?: (contradictionId: string) => void
}

export function ContradictionDisplay({
  contradictions,
  onAskClarification,
  onMarkResolved,
}: ContradictionDisplayProps) {
  // Group by severity
  const highSeverity = contradictions.filter((c) => c.severity === "HIGH")
  const mediumSeverity = contradictions.filter((c) => c.severity === "MEDIUM")
  const lowSeverity = contradictions.filter((c) => c.severity === "LOW")

  // Group by status
  const unresolved = contradictions.filter((c) => c.resolution_status === "UNRESOLVED")
  const clarified = contradictions.filter((c) => c.resolution_status === "CLARIFIED")
  const confirmed = contradictions.filter((c) => c.resolution_status === "CONFIRMED")

  return (
    <div className="app-surface" style={styles.container}>
      <div style={styles.header}>
        <div style={styles.title}>Contradictions Detected</div>
        <div style={styles.summary}>
          <span style={styles.summaryItem}>
            Total: <strong>{contradictions.length}</strong>
          </span>
          <span style={styles.summaryDivider}>·</span>
          <span style={styles.summaryItem}>
            Unresolved: <strong style={{ color: "#dc2626" }}>{unresolved.length}</strong>
          </span>
          <span style={styles.summaryDivider}>·</span>
          <span style={styles.summaryItem}>
            Clarified: <strong>{clarified.length}</strong>
          </span>
          <span style={styles.summaryDivider}>·</span>
          <span style={styles.summaryItem}>
            Confirmed: <strong>{confirmed.length}</strong>
          </span>
        </div>
      </div>

      {contradictions.length === 0 ? (
        <div style={styles.emptyState}>
          ✓ No contradictions detected. All evidence is consistent.
        </div>
      ) : (
        <>
          {highSeverity.length > 0 && (
            <div style={styles.section}>
              <div style={styles.sectionTitle}>
                <span style={{ ...styles.severityBadge, ...styles.highSeverity }}>HIGH</span>
                High Severity ({highSeverity.length})
              </div>
              {highSeverity.map((contradiction) => (
                <ContradictionCard
                  key={contradiction.contradiction_id}
                  contradiction={contradiction}
                  onAskClarification={onAskClarification}
                  onMarkResolved={onMarkResolved}
                />
              ))}
            </div>
          )}

          {mediumSeverity.length > 0 && (
            <div style={styles.section}>
              <div style={styles.sectionTitle}>
                <span style={{ ...styles.severityBadge, ...styles.mediumSeverity }}>MEDIUM</span>
                Medium Severity ({mediumSeverity.length})
              </div>
              {mediumSeverity.map((contradiction) => (
                <ContradictionCard
                  key={contradiction.contradiction_id}
                  contradiction={contradiction}
                  onAskClarification={onAskClarification}
                  onMarkResolved={onMarkResolved}
                />
              ))}
            </div>
          )}

          {lowSeverity.length > 0 && (
            <div style={styles.section}>
              <div style={styles.sectionTitle}>
                <span style={{ ...styles.severityBadge, ...styles.lowSeverity }}>LOW</span>
                Low Severity ({lowSeverity.length})
              </div>
              {lowSeverity.map((contradiction) => (
                <ContradictionCard
                  key={contradiction.contradiction_id}
                  contradiction={contradiction}
                  onAskClarification={onAskClarification}
                  onMarkResolved={onMarkResolved}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

interface ContradictionCardProps {
  contradiction: Contradiction
  onAskClarification?: (contradictionId: string, question: string) => void
  onMarkResolved?: (contradictionId: string) => void
}

function ContradictionCard({
  contradiction,
  onAskClarification,
  onMarkResolved,
}: ContradictionCardProps) {
  const isUnresolved = contradiction.resolution_status === "UNRESOLVED"
  const severityColor = getSeverityColor(contradiction.severity)

  return (
    <div
      style={{
        ...styles.card,
        borderLeft: `4px solid ${severityColor}`,
      }}
    >
      <div style={styles.cardHeader}>
        <div style={styles.cardTitle}>
          ⚠️ {contradiction.contradiction_type} Contradiction
        </div>
        <div style={styles.cardMeta}>
          <span
            style={{
              ...styles.statusBadge,
              backgroundColor: isUnresolved ? "#fef2f2" : "#f0fdf4",
              color: isUnresolved ? "#dc2626" : "#16a34a",
            }}
          >
            {contradiction.resolution_status}
          </span>
          <span style={styles.cardTime}>{formatDate(contradiction.created_at)}</span>
        </div>
      </div>

      <div style={styles.description}>{contradiction.description}</div>

      <div style={styles.answersSection}>
        <div style={styles.answersLabel}>Conflicting Answers:</div>
        {contradiction.conflicting_answers.map((answer, index) => (
          <div key={answer.answer_id} style={styles.answerBox}>
            <div style={styles.answerHeader}>
              Answer {index + 1} ({answer.answer_id})
            </div>
            <div style={styles.answerText}>"{answer.text}"</div>
          </div>
        ))}
      </div>

      {contradiction.clarification_question && (
        <div style={styles.clarificationSection}>
          <div style={styles.clarificationLabel}>Suggested Clarification:</div>
          <div style={styles.clarificationText}>
            {contradiction.clarification_question}
          </div>
        </div>
      )}

      {isUnresolved && (
        <div style={styles.actions}>
          {onAskClarification && contradiction.clarification_question && (
            <button
              onClick={() =>
                onAskClarification(
                  contradiction.contradiction_id,
                  contradiction.clarification_question!,
                )
              }
              style={styles.primaryButton}
            >
              Ask Clarification
            </button>
          )}
          {onMarkResolved && (
            <button
              onClick={() => onMarkResolved(contradiction.contradiction_id)}
              style={styles.secondaryButton}
            >
              Mark Resolved
            </button>
          )}
        </div>
      )}
    </div>
  )
}

function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    HIGH: "#dc2626",
    MEDIUM: "#ea580c",
    LOW: "#eab308",
  }
  return colors[severity] || "#64748b"
}

function formatDate(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: "1.35rem 1.45rem",
  },
  header: {
    marginBottom: "1.5rem",
  },
  title: {
    fontSize: "1.1rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
    marginBottom: "0.75rem",
  },
  summary: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    fontSize: "0.85rem",
    color: "var(--wj-text-secondary)",
  },
  summaryItem: {},
  summaryDivider: {
    color: "var(--wj-text-tertiary)",
  },
  emptyState: {
    padding: "2rem",
    textAlign: "center",
    color: "var(--wj-success)",
    fontSize: "0.95rem",
    backgroundColor: "#f0fdf4",
    borderRadius: "0.5rem",
  },
  section: {
    marginBottom: "1.5rem",
  },
  sectionTitle: {
    display: "flex",
    alignItems: "center",
    gap: "0.75rem",
    fontSize: "0.9rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
    marginBottom: "0.85rem",
  },
  severityBadge: {
    padding: "0.25rem 0.6rem",
    borderRadius: "0.25rem",
    fontSize: "0.7rem",
    fontWeight: 700,
    letterSpacing: "0.05em",
  },
  highSeverity: {
    backgroundColor: "#fef2f2",
    color: "#dc2626",
  },
  mediumSeverity: {
    backgroundColor: "#fff7ed",
    color: "#ea580c",
  },
  lowSeverity: {
    backgroundColor: "#fefce8",
    color: "#ca8a04",
  },
  card: {
    padding: "1.15rem",
    backgroundColor: "var(--wj-bg-subtle)",
    borderRadius: "0.5rem",
    marginBottom: "0.85rem",
  },
  cardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: "1rem",
    marginBottom: "0.75rem",
  },
  cardTitle: {
    fontSize: "0.95rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
  },
  cardMeta: {
    display: "flex",
    alignItems: "center",
    gap: "0.75rem",
  },
  statusBadge: {
    padding: "0.25rem 0.6rem",
    borderRadius: 999,
    fontSize: "0.7rem",
    fontWeight: 600,
    textTransform: "uppercase",
  },
  cardTime: {
    fontSize: "0.75rem",
    color: "var(--wj-text-tertiary)",
    whiteSpace: "nowrap",
  },
  description: {
    fontSize: "0.9rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.6,
    marginBottom: "1rem",
  },
  answersSection: {
    marginBottom: "1rem",
  },
  answersLabel: {
    fontSize: "0.82rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
    marginBottom: "0.6rem",
  },
  answerBox: {
    padding: "0.75rem",
    backgroundColor: "var(--wj-bg)",
    borderRadius: "0.375rem",
    marginBottom: "0.6rem",
    border: "1px solid var(--wj-border)",
  },
  answerHeader: {
    fontSize: "0.75rem",
    color: "var(--wj-text-tertiary)",
    marginBottom: "0.4rem",
    fontFamily: '"JetBrains Mono", Consolas, monospace',
  },
  answerText: {
    fontSize: "0.85rem",
    color: "var(--wj-text-primary)",
    lineHeight: 1.6,
    fontStyle: "italic",
  },
  clarificationSection: {
    padding: "0.85rem",
    backgroundColor: "#eff6ff",
    borderRadius: "0.375rem",
    marginBottom: "1rem",
  },
  clarificationLabel: {
    fontSize: "0.78rem",
    fontWeight: 600,
    color: "#1e40af",
    marginBottom: "0.45rem",
  },
  clarificationText: {
    fontSize: "0.88rem",
    color: "#1e3a8a",
    lineHeight: 1.6,
  },
  actions: {
    display: "flex",
    gap: "0.75rem",
  },
  primaryButton: {
    padding: "0.5rem 1rem",
    backgroundColor: "var(--wj-brand-primary)",
    color: "white",
    border: "none",
    borderRadius: "0.375rem",
    fontSize: "0.85rem",
    fontWeight: 500,
    cursor: "pointer",
    transition: "all 0.15s",
  },
  secondaryButton: {
    padding: "0.5rem 1rem",
    backgroundColor: "transparent",
    color: "var(--wj-text-secondary)",
    border: "1px solid var(--wj-border)",
    borderRadius: "0.375rem",
    fontSize: "0.85rem",
    fontWeight: 500,
    cursor: "pointer",
    transition: "all 0.15s",
  },
}
