import React from "react"
import type { EvidenceTransition } from "../api/evidence-api"

interface EvidenceTimelineProps {
  verificationPointId: string
  aspect: string
  currentState: string
  transitions: EvidenceTransition[]
}

export function EvidenceTimeline({
  aspect,
  currentState,
  transitions,
}: EvidenceTimelineProps) {
  // Sort transitions by created_at (oldest first)
  const sortedTransitions = [...transitions].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  )

  return (
    <div className="app-surface" style={styles.container}>
      <div style={styles.header}>
        <div style={styles.title}>Evidence Timeline</div>
        <div style={styles.subtitle}>{aspect}</div>
        <div style={styles.currentState}>
          Current State: <span style={styles.stateBadge}>{currentState}</span>
        </div>
      </div>

      <div style={styles.timeline}>
        {sortedTransitions.map((transition, index) => (
          <div key={transition.transition_id} style={styles.timelineItem}>
            <div style={styles.timelineMarker}>
              <div
                style={{
                  ...styles.markerDot,
                  backgroundColor: getStateColor(transition.to_state),
                }}
              />
              {index < sortedTransitions.length - 1 && <div style={styles.markerLine} />}
            </div>

            <div style={styles.timelineContent}>
              <div style={styles.timelineTime}>{formatDateTime(transition.created_at)}</div>

              <div style={styles.transitionBox}>
                <div style={styles.stateTransition}>
                  <span style={styles.fromState}>{transition.from_state}</span>
                  <span style={styles.arrow}>→</span>
                  <span
                    style={{
                      ...styles.toState,
                      color: getStateColor(transition.to_state),
                    }}
                  >
                    {transition.to_state}
                  </span>
                </div>

                <div style={styles.reasonCode}>
                  Reason: <code style={styles.code}>{transition.reason_code}</code>
                </div>

                {transition.answer_id && (
                  <div style={styles.answerId}>
                    Answer: <code style={styles.code}>{transition.answer_id}</code>
                  </div>
                )}

                {transition.evidence_spans && transition.evidence_spans.length > 0 && (
                  <div style={styles.evidenceSection}>
                    <div style={styles.evidenceLabel}>Evidence:</div>
                    {transition.evidence_spans.map((span, spanIndex) => (
                      <div key={spanIndex} style={styles.evidenceSpan}>
                        <div style={styles.spanText}>"{span.text}"</div>
                        <div style={styles.spanMeta}>
                          Position: {span.start}–{span.end} · Hash: {span.quote_hash.slice(0, 12)}...
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div style={styles.policyVersion}>
                  Policy: v{transition.policy_version}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {sortedTransitions.length === 0 && (
        <div style={styles.emptyState}>No state transitions recorded yet.</div>
      )}
    </div>
  )
}

function getStateColor(state: string): string {
  const colors: Record<string, string> = {
    VERIFIED: "#16a34a",
    PARTIALLY_SUPPORTED: "#ea580c",
    CONTRADICTORY: "#dc2626",
    ADDRESSED: "#2563eb",
    UNSEEN: "#94a3b8",
    UNSUPPORTED: "#991b1b",
  }
  return colors[state] || "#64748b"
}

function formatDateTime(isoString: string): string {
  const date = new Date(isoString)
  const timeStr = date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  })
  const dateStr = date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  })
  return `${timeStr} · ${dateStr}`
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
    marginBottom: "0.4rem",
  },
  subtitle: {
    fontSize: "0.9rem",
    color: "var(--wj-text-secondary)",
    marginBottom: "0.75rem",
  },
  currentState: {
    fontSize: "0.85rem",
    color: "var(--wj-text-secondary)",
  },
  stateBadge: {
    fontWeight: 600,
    color: "var(--wj-text-primary)",
  },
  timeline: {
    display: "flex",
    flexDirection: "column",
  },
  timelineItem: {
    display: "flex",
    gap: "1rem",
  },
  timelineMarker: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    paddingTop: "0.35rem",
  },
  markerDot: {
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    border: "2px solid white",
    boxShadow: "0 0 0 2px currentColor",
    flexShrink: 0,
  },
  markerLine: {
    width: "2px",
    flexGrow: 1,
    backgroundColor: "var(--wj-border)",
    marginTop: "0.25rem",
    marginBottom: "0.25rem",
  },
  timelineContent: {
    flexGrow: 1,
    paddingBottom: "1.5rem",
  },
  timelineTime: {
    fontSize: "0.78rem",
    color: "var(--wj-text-tertiary)",
    marginBottom: "0.5rem",
    fontFamily: '"JetBrains Mono", Consolas, monospace',
  },
  transitionBox: {
    padding: "1rem",
    backgroundColor: "var(--wj-bg-subtle)",
    borderRadius: "0.5rem",
    display: "flex",
    flexDirection: "column",
    gap: "0.65rem",
  },
  stateTransition: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    fontSize: "0.9rem",
    fontWeight: 600,
  },
  fromState: {
    color: "var(--wj-text-secondary)",
  },
  arrow: {
    color: "var(--wj-text-tertiary)",
  },
  toState: {
    fontWeight: 700,
  },
  reasonCode: {
    fontSize: "0.82rem",
    color: "var(--wj-text-secondary)",
  },
  answerId: {
    fontSize: "0.82rem",
    color: "var(--wj-text-secondary)",
  },
  code: {
    fontFamily: '"JetBrains Mono", Consolas, monospace',
    fontSize: "0.8rem",
    padding: "0.15rem 0.4rem",
    backgroundColor: "var(--wj-bg)",
    borderRadius: "0.25rem",
    color: "var(--wj-text-primary)",
  },
  evidenceSection: {
    marginTop: "0.25rem",
  },
  evidenceLabel: {
    fontSize: "0.82rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
    marginBottom: "0.5rem",
  },
  evidenceSpan: {
    marginBottom: "0.75rem",
  },
  spanText: {
    fontSize: "0.85rem",
    color: "var(--wj-text-primary)",
    lineHeight: 1.6,
    fontStyle: "italic",
    marginBottom: "0.35rem",
  },
  spanMeta: {
    fontSize: "0.72rem",
    color: "var(--wj-text-tertiary)",
    fontFamily: '"JetBrains Mono", Consolas, monospace',
  },
  policyVersion: {
    fontSize: "0.72rem",
    color: "var(--wj-text-tertiary)",
  },
  emptyState: {
    padding: "2rem",
    textAlign: "center",
    color: "var(--wj-text-tertiary)",
    fontSize: "0.9rem",
  },
}
