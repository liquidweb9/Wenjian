import React, { useState } from "react"
import { ClaimStatusCard } from "./ClaimStatusCard"
import { EvidenceTimeline } from "./EvidenceTimeline"
import { EvidenceSpanViewer } from "./EvidenceSpanViewer"
import { useVerificationPoints, useTransitions, useEvidence } from "../hooks/use-evidence"
import type { ClaimItem } from "@/features/resumes/api/resume-api"

interface ClaimPassportProps {
  claims: ClaimItem[]
  interviewId: string
}

/**
 * Claim Passport - Phase 2.2 Evidence Visualization
 *
 * Displays claim verification status with evidence traceability:
 * - Claim status cards with verification point summaries
 * - Evidence timeline showing state transitions
 * - Evidence span viewer linking to specific Q&A
 */
export function ClaimPassport({ claims, interviewId }: ClaimPassportProps) {
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null)
  const [selectedVpId, setSelectedVpId] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<"timeline" | "evidence">("timeline")

  // Fetch verification points for selected claim
  const { data: vpData } = useVerificationPoints(selectedClaimId || undefined)
  const verificationPoints = vpData?.verification_points || []

  // Fetch transitions for selected VP
  const { data: transitionsData } = useTransitions(selectedVpId || undefined)

  // Fetch evidence for selected VP
  const { data: evidenceData } = useEvidence(selectedVpId || undefined)

  const handleClaimClick = (claimId: string) => {
    if (selectedClaimId === claimId) {
      // Collapse if clicking the same claim
      setSelectedClaimId(null)
      setSelectedVpId(null)
    } else {
      setSelectedClaimId(claimId)
      setSelectedVpId(null) // Reset VP selection when switching claims
    }
  }

  const handleViewTimeline = (vpId: string) => {
    setSelectedVpId(vpId)
    setViewMode("timeline")
  }

  const handleViewEvidence = (vpId: string) => {
    setSelectedVpId(vpId)
    setViewMode("evidence")
  }

  const handleCloseModal = () => {
    setSelectedVpId(null)
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={styles.headerContent}>
          <h3 style={styles.title}>Claim Passport</h3>
          <p style={styles.subtitle}>
            证据追溯：查看每个简历陈述的验证状态、证据时间线和对应的面试问答
          </p>
        </div>
        <div style={styles.legend}>
          <LegendItem icon="✓" color="#16a34a" label="已验证" />
          <LegendItem icon="◐" color="#ea580c" label="部分支持" />
          <LegendItem icon="◯" color="#2563eb" label="已涉及" />
          <LegendItem icon="⚠" color="#dc2626" label="矛盾" />
          <LegendItem icon="−" color="#94a3b8" label="未涉及" />
        </div>
      </div>

      {claims.length === 0 ? (
        <div style={styles.emptyState}>
          <p style={styles.emptyText}>暂无简历陈述数据</p>
        </div>
      ) : (
        <div style={styles.claimList}>
          {claims.map((claim) => {
            const claimData = claim.data as Record<string, unknown>
            const claimText = (claimData.claim_text as string) || `Claim ${claim.claim_id.slice(0, 8)}`
            const isSelected = selectedClaimId === claim.claim_id
            const vpsForClaim = isSelected ? verificationPoints : []

            return (
              <div key={claim.claim_id} style={styles.claimItem}>
                <button
                  onClick={() => handleClaimClick(claim.claim_id)}
                  style={{
                    ...styles.claimButton,
                    ...(isSelected ? styles.claimButtonActive : {}),
                  }}
                >
                  <div style={styles.claimHeader}>
                    <span style={styles.claimText}>{claimText}</span>
                    <span style={styles.expandIcon}>{isSelected ? "▼" : "▶"}</span>
                  </div>
                  <div style={styles.claimMeta}>
                    <span style={styles.claimMetaItem}>优先级: {claim.priority}</span>
                    <span style={styles.claimMetaItem}>
                      置信度: {Math.round(claim.confidence * 100)}%
                    </span>
                  </div>
                </button>

                {isSelected && vpsForClaim.length > 0 && (
                  <div style={styles.claimDetails}>
                    <ClaimStatusCard
                      claimId={claim.claim_id}
                      claimText={claimText}
                      verificationPoints={vpsForClaim}
                      onViewTimeline={handleViewTimeline}
                    />

                    {/* Add evidence viewer button */}
                    <div style={styles.actionBar}>
                      {vpsForClaim.map((vp) => (
                        <button
                          key={vp.verification_point_id}
                          onClick={() => handleViewEvidence(vp.verification_point_id)}
                          style={styles.evidenceButton}
                        >
                          查看 "{vp.aspect}" 的证据片段 →
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Modal for timeline/evidence view */}
      {selectedVpId && (
        <div style={styles.modal} onClick={handleCloseModal}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <button style={styles.closeButton} onClick={handleCloseModal}>
              ✕
            </button>

            {/* Toggle between timeline and evidence views */}
            <div style={styles.modalTabs}>
              <button
                onClick={() => setViewMode("timeline")}
                style={{
                  ...styles.tab,
                  ...(viewMode === "timeline" ? styles.tabActive : {}),
                }}
              >
                状态时间线
              </button>
              <button
                onClick={() => setViewMode("evidence")}
                style={{
                  ...styles.tab,
                  ...(viewMode === "evidence" ? styles.tabActive : {}),
                }}
              >
                证据片段
              </button>
            </div>

            <div style={styles.modalBody}>
              {viewMode === "timeline" && transitionsData && (
                <EvidenceTimeline
                  verificationPointId={transitionsData.verification_point_id}
                  aspect={transitionsData.verification_point_id}
                  currentState={transitionsData.current_state}
                  transitions={transitionsData.transitions}
                />
              )}

              {viewMode === "evidence" && evidenceData && (
                <EvidenceSpanViewer
                  verificationPointId={evidenceData.verification_point_id}
                  aspect={evidenceData.aspect}
                  currentState={evidenceData.current_state}
                  evidence={evidenceData.evidence}
                  interviewId={interviewId}
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function LegendItem({
  icon,
  color,
  label,
}: {
  icon: string
  color: string
  label: string
}) {
  return (
    <div style={styles.legendItem}>
      <span style={{ ...styles.legendIcon, color }}>{icon}</span>
      <span style={styles.legendLabel}>{label}</span>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "grid",
    gap: "1rem",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: "1.5rem",
    flexWrap: "wrap",
  },
  headerContent: {
    flex: 1,
    minWidth: 300,
  },
  title: {
    margin: 0,
    fontSize: "1.2rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
  },
  subtitle: {
    margin: "0.5rem 0 0",
    fontSize: "0.88rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.6,
  },
  legend: {
    display: "flex",
    gap: "1rem",
    flexWrap: "wrap",
  },
  legendItem: {
    display: "flex",
    alignItems: "center",
    gap: "0.35rem",
  },
  legendIcon: {
    fontSize: "1rem",
    fontWeight: 600,
  },
  legendLabel: {
    fontSize: "0.8rem",
    color: "var(--wj-text-secondary)",
  },
  emptyState: {
    padding: "2rem",
    textAlign: "center",
  },
  emptyText: {
    margin: 0,
    color: "var(--wj-text-secondary)",
    fontSize: "0.9rem",
  },
  claimList: {
    display: "grid",
    gap: "0.75rem",
  },
  claimItem: {
    display: "grid",
    gap: "0.75rem",
  },
  claimButton: {
    width: "100%",
    padding: "1rem 1.25rem",
    backgroundColor: "var(--wj-bg-surface)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.75rem",
    textAlign: "left",
    cursor: "pointer",
    transition: "all 0.15s",
  },
  claimButtonActive: {
    backgroundColor: "var(--wj-brand-accent-bg)",
    borderColor: "var(--wj-brand-secondary)",
  },
  claimHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "1rem",
  },
  claimText: {
    flex: 1,
    fontSize: "0.95rem",
    fontWeight: 500,
    color: "var(--wj-text-primary)",
    lineHeight: 1.6,
  },
  expandIcon: {
    fontSize: "0.75rem",
    color: "var(--wj-text-tertiary)",
  },
  claimMeta: {
    display: "flex",
    gap: "1rem",
    marginTop: "0.5rem",
    fontSize: "0.8rem",
  },
  claimMetaItem: {
    color: "var(--wj-text-secondary)",
  },
  claimDetails: {
    display: "grid",
    gap: "0.75rem",
    paddingLeft: "1rem",
  },
  actionBar: {
    display: "grid",
    gap: "0.5rem",
  },
  evidenceButton: {
    padding: "0.6rem 1rem",
    backgroundColor: "transparent",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.5rem",
    color: "var(--wj-brand-primary)",
    fontSize: "0.85rem",
    fontWeight: 500,
    cursor: "pointer",
    textAlign: "left",
    transition: "all 0.15s",
  },
  modal: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
    padding: "1rem",
  },
  modalContent: {
    position: "relative",
    width: "100%",
    maxWidth: 900,
    maxHeight: "90vh",
    backgroundColor: "var(--wj-bg-surface)",
    borderRadius: "1rem",
    boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    overflow: "hidden",
    display: "flex",
    flexDirection: "column",
  },
  closeButton: {
    position: "absolute",
    top: "1rem",
    right: "1rem",
    width: 32,
    height: 32,
    display: "grid",
    placeItems: "center",
    backgroundColor: "var(--wj-bg-subtle)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.375rem",
    color: "var(--wj-text-secondary)",
    fontSize: "1.2rem",
    cursor: "pointer",
    transition: "all 0.15s",
    zIndex: 10,
  },
  modalTabs: {
    display: "flex",
    gap: "0.25rem",
    padding: "1rem 1rem 0",
    borderBottom: "1px solid var(--wj-border-subtle)",
  },
  tab: {
    padding: "0.75rem 1.25rem",
    backgroundColor: "transparent",
    border: "none",
    borderBottom: "2px solid transparent",
    color: "var(--wj-text-secondary)",
    fontSize: "0.9rem",
    fontWeight: 500,
    cursor: "pointer",
    transition: "all 0.15s",
  },
  tabActive: {
    color: "var(--wj-brand-primary)",
    borderBottomColor: "var(--wj-brand-primary)",
  },
  modalBody: {
    flex: 1,
    overflowY: "auto",
    padding: "1.5rem",
  },
}
