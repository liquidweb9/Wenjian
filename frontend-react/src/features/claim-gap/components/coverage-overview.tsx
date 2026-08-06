import React from "react"
import type { GapAnalysisResult } from "@/lib/types/claim-gap"

interface CoverageOverviewProps {
  analysis: GapAnalysisResult
}

export function CoverageOverview({ analysis }: CoverageOverviewProps) {
  const { coverage_stats: stats } = analysis

  const coveragePercent = Math.round(stats.coverage_percentage * 100)
  const coverageColor = getCoverageColor(stats.coverage_percentage)

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>能力覆盖概览</h2>
      </div>

      <div style={styles.mainScore}>
        <div style={styles.scoreCircle}>
          <svg width="160" height="160" viewBox="0 0 160 160">
            <circle
              cx="80"
              cy="80"
              r="70"
              fill="none"
              stroke="#f3f4f6"
              strokeWidth="12"
            />
            <circle
              cx="80"
              cy="80"
              r="70"
              fill="none"
              stroke={coverageColor}
              strokeWidth="12"
              strokeDasharray={`${2 * Math.PI * 70}`}
              strokeDashoffset={`${2 * Math.PI * 70 * (1 - stats.coverage_percentage)}`}
              strokeLinecap="round"
              transform="rotate(-90 80 80)"
              style={{ transition: "stroke-dashoffset 0.6s ease" }}
            />
          </svg>
          <div style={styles.scoreText}>
            <div style={{ ...styles.scoreValue, color: coverageColor }}>{coveragePercent}%</div>
            <div style={styles.scoreLabel}>整体覆盖</div>
          </div>
        </div>

        <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <div style={styles.statValue}>{stats.covered_requirements}</div>
            <div style={styles.statLabel}>已覆盖需求</div>
            <div style={styles.statTotal}>/ {stats.total_requirements}</div>
          </div>

          <div style={styles.statCard}>
            <div style={{ ...styles.statValue, color: "#dc2626" }}>
              {stats.uncovered_requirements}
            </div>
            <div style={styles.statLabel}>未覆盖需求</div>
          </div>

          <div style={styles.statCard}>
            <div style={{ ...styles.statValue, color: "#059669" }}>
              {stats.high_priority_gaps}
            </div>
            <div style={styles.statLabel}>高优先级缺口</div>
          </div>

          <div style={styles.statCard}>
            <div style={{ ...styles.statValue, color: "#d97706" }}>
              {stats.weak_evidence_count}
            </div>
            <div style={styles.statLabel}>证据薄弱</div>
          </div>
        </div>
      </div>
    </div>
  )
}

function getCoverageColor(coverage: number): string {
  if (coverage >= 0.8) return "#059669" // Green
  if (coverage >= 0.6) return "#d97706" // Orange
  return "#dc2626" // Red
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
    margin: 0,
  },
  mainScore: {
    display: "flex",
    gap: "32px",
    alignItems: "center",
  },
  scoreCircle: {
    position: "relative",
    flexShrink: 0,
  },
  scoreText: {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    textAlign: "center",
  },
  scoreValue: {
    fontSize: "36px",
    fontWeight: 700,
    lineHeight: 1,
    marginBottom: "4px",
  },
  scoreLabel: {
    fontSize: "13px",
    color: "#6b7280",
    fontWeight: 500,
  },
  statsGrid: {
    flex: 1,
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
    gap: "16px",
  },
  statCard: {
    padding: "16px",
    backgroundColor: "#f9fafb",
    borderRadius: "8px",
    textAlign: "center",
  },
  statValue: {
    fontSize: "28px",
    fontWeight: 700,
    color: "#1a1a1a",
    lineHeight: 1,
    marginBottom: "6px",
  },
  statLabel: {
    fontSize: "12px",
    color: "#6b7280",
    fontWeight: 500,
    marginBottom: "2px",
  },
  statTotal: {
    fontSize: "11px",
    color: "#9ca3af",
  },
}
