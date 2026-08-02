import React from "react"
import type { VerificationPoint } from "../api/evidence-api"

interface ClaimStatusCardProps {
  claimId: string
  claimText: string
  verificationPoints: VerificationPoint[]
  onViewTimeline?: (verificationPointId: string) => void
}

export function ClaimStatusCard({
  claimId,
  claimText,
  verificationPoints,
  onViewTimeline,
}: ClaimStatusCardProps) {
  // Calculate overall status
  const verifiedCount = verificationPoints.filter((vp) => vp.current_state === "VERIFIED").length
  const partialCount = verificationPoints.filter((vp) => vp.current_state === "PARTIALLY_SUPPORTED").length
  const contradictionCount = verificationPoints.filter((vp) => vp.has_contradictions).length
  const totalCount = verificationPoints.length

  // Determine overall status
  let overallStatus = "UNSEEN"
  let statusColor = "#94a3b8"
  let statusBg = "#f1f5f9"

  if (contradictionCount > 0) {
    overallStatus = "CONTRADICTORY"
    statusColor = "#dc2626"
    statusBg = "#fef2f2"
  } else if (verifiedCount === totalCount && totalCount > 0) {
    overallStatus = "VERIFIED"
    statusColor = "#16a34a"
    statusBg = "#f0fdf4"
  } else if (verifiedCount > 0 || partialCount > 0) {
    overallStatus = "PARTIALLY_SUPPORTED"
    statusColor = "#ea580c"
    statusBg = "#fff7ed"
  } else if (totalCount > 0) {
    overallStatus = "ADDRESSED"
    statusColor = "#2563eb"
    statusBg = "#eff6ff"
  }

  // Calculate average confidence
  const confidenceScores = verificationPoints
    .filter((vp) => vp.strength !== null)
    .map((vp) => vp.strength!)
  const avgConfidence = confidenceScores.length > 0
    ? confidenceScores.reduce((sum, score) => sum + score, 0) / confidenceScores.length
    : null

  const confidenceLevel = avgConfidence !== null
    ? avgConfidence >= 0.8 ? "HIGH" : avgConfidence >= 0.5 ? "MEDIUM" : "LOW"
    : null

  // Total evidence count
  const totalEvidence = verificationPoints.reduce((sum, vp) => sum + vp.evidence_count, 0)

  // Most recent update
  const mostRecent = verificationPoints.reduce((latest, vp) => {
    return !latest || new Date(vp.updated_at) > new Date(latest) ? vp.updated_at : latest
  }, "")

  const timeAgo = mostRecent ? formatTimeAgo(mostRecent) : null

  return (
    <div className="app-surface" style={styles.card}>
      <div style={styles.header}>
        <div style={styles.claimText}>{claimText}</div>
        <div style={styles.claimId}>{claimId}</div>
      </div>

      <div style={styles.statusRow}>
        <div style={styles.statusLabel}>Status:</div>
        <span style={{ ...styles.statusPill, backgroundColor: statusBg, color: statusColor }}>
          {getStatusIcon(overallStatus)} {overallStatus}
        </span>
      </div>

      {confidenceLevel && (
        <div style={styles.metaRow}>
          <span style={styles.metaLabel}>Confidence:</span>
          <span style={styles.metaValue}>
            {confidenceLevel} ({avgConfidence !== null ? Math.round(avgConfidence * 100) : 0}%)
          </span>
        </div>
      )}

      <div style={styles.metaRow}>
        <span style={styles.metaLabel}>Verification Points:</span>
        <span style={styles.metaValue}>
          {verifiedCount}/{totalCount} verified
        </span>
      </div>

      <div style={styles.metaRow}>
        <span style={styles.metaLabel}>Evidence Count:</span>
        <span style={styles.metaValue}>{totalEvidence} pieces</span>
      </div>

      {timeAgo && (
        <div style={styles.metaRow}>
          <span style={styles.metaLabel}>Last Updated:</span>
          <span style={styles.metaValue}>{timeAgo}</span>
        </div>
      )}

      {contradictionCount > 0 && (
        <div style={styles.warningBox}>
          ⚠️ {contradictionCount} contradiction{contradictionCount > 1 ? "s" : ""} detected
        </div>
      )}

      {verificationPoints.length > 0 && (
        <div style={styles.vpList}>
          {verificationPoints.map((vp) => (
            <div key={vp.verification_point_id} style={styles.vpItem}>
              <div style={styles.vpAspect}>{vp.aspect}</div>
              <div style={styles.vpMeta}>
                <span style={styles.vpState}>{vp.current_state}</span>
                {vp.has_contradictions && <span style={styles.vpWarning}>⚠️</span>}
              </div>
              {onViewTimeline && (
                <button
                  onClick={() => onViewTimeline(vp.verification_point_id)}
                  style={styles.viewButton}
                >
                  View Timeline →
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function getStatusIcon(status: string): string {
  const icons: Record<string, string> = {
    VERIFIED: "✓",
    PARTIALLY_SUPPORTED: "◐",
    CONTRADICTORY: "⚠",
    ADDRESSED: "◯",
    UNSEEN: "−",
  }
  return icons[status] || "·"
}

function formatTimeAgo(isoString: string): string {
  const now = new Date()
  const then = new Date(isoString)
  const diffMs = now.getTime() - then.getTime()
  const diffMinutes = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMinutes < 1) return "just now"
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    padding: "1.35rem 1.45rem",
  },
  header: {
    marginBottom: "1rem",
  },
  claimText: {
    fontSize: "1.05rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
    lineHeight: 1.6,
    marginBottom: "0.5rem",
  },
  claimId: {
    fontSize: "0.78rem",
    color: "var(--wj-text-tertiary)",
    fontFamily: '"JetBrains Mono", Consolas, monospace',
  },
  statusRow: {
    display: "flex",
    alignItems: "center",
    gap: "0.75rem",
    marginBottom: "0.85rem",
  },
  statusLabel: {
    fontSize: "0.9rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
  },
  statusPill: {
    padding: "0.3rem 0.75rem",
    borderRadius: 999,
    fontSize: "0.8rem",
    fontWeight: 600,
  },
  metaRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "0.5rem",
    fontSize: "0.85rem",
  },
  metaLabel: {
    color: "var(--wj-text-secondary)",
  },
  metaValue: {
    color: "var(--wj-text-primary)",
    fontWeight: 500,
  },
  warningBox: {
    marginTop: "1rem",
    padding: "0.75rem 1rem",
    backgroundColor: "#fef2f2",
    color: "#dc2626",
    borderRadius: "0.5rem",
    fontSize: "0.85rem",
    fontWeight: 500,
  },
  vpList: {
    marginTop: "1.25rem",
    display: "grid",
    gap: "0.75rem",
  },
  vpItem: {
    padding: "0.85rem 1rem",
    backgroundColor: "var(--wj-bg-subtle)",
    borderRadius: "0.5rem",
    display: "flex",
    flexDirection: "column",
    gap: "0.5rem",
  },
  vpAspect: {
    fontSize: "0.9rem",
    fontWeight: 500,
    color: "var(--wj-text-primary)",
  },
  vpMeta: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
  },
  vpState: {
    fontSize: "0.75rem",
    color: "var(--wj-text-tertiary)",
    textTransform: "uppercase",
  },
  vpWarning: {
    fontSize: "0.9rem",
  },
  viewButton: {
    alignSelf: "flex-start",
    marginTop: "0.25rem",
    padding: "0.35rem 0.75rem",
    backgroundColor: "transparent",
    border: "1px solid var(--wj-border)",
    borderRadius: "0.375rem",
    color: "var(--wj-brand-primary)",
    fontSize: "0.8rem",
    fontWeight: 500,
    cursor: "pointer",
    transition: "all 0.15s",
  },
}
