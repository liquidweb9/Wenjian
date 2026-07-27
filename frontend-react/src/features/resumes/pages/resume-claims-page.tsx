import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useResumeClaims, useUpdateClaim } from "../hooks/use-resumes"

const riskLabels: Record<string, string> = {
  UNVERIFIED_IMPROVEMENT: "未验证改进",
  MISSING_METRICS: "缺少量化指标",
  UNCLEAR_OWNERSHIP: "贡献不明确",
  TECH_STACK_DENSITY: "技术栈密度",
}

const riskColors: Record<string, string> = {
  UNVERIFIED_IMPROVEMENT: "#f59e0b",
  MISSING_METRICS: "#e63946",
  UNCLEAR_OWNERSHIP: "#f59e0b",
  TECH_STACK_DENSITY: "#3b82f6",
}

export default function ResumeClaimsPage() {
  const { resumeId } = useParams<{ resumeId: string }>()
  const navigate = useNavigate()
  const { data, isLoading, isError } = useResumeClaims(resumeId)
  const updateClaim = useUpdateClaim()

  const [expanded, setExpanded] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>("")

  if (isLoading) {
    return <div style={{ padding: "2rem", textAlign: "center", color: "#64748b" }}>加载中...</div>
  }

  if (isError || !data) {
    return (
      <div style={{ padding: "2rem", textAlign: "center" }}>
        <p style={{ color: "#e63946" }}>加载主张失败</p>
        <button onClick={() => navigate(`/app/resumes/${resumeId}/review`)}>返回</button>
      </div>
    )
  }

  const claims = data.claims || []
  const types = [...new Set(claims.map((c) => (c.data as Record<string, unknown>)?.claim_type as string || "未知"))]

  const filtered = claims.filter((c) => {
    if (!filter) return true
    const ctype = (c.data as Record<string, unknown>)?.claim_type as string || ""
    return ctype === filter
  })

  async function toggleClaim(claimId: string, disabled: boolean) {
    await updateClaim.mutateAsync({
      resumeId: resumeId!,
      claimId,
      updates: { enabled: !disabled },
    })
  }

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1.5rem" }}>
        <button
          onClick={() => navigate(`/app/resumes/${resumeId}/profile`)}
          style={{
            padding: "0.4rem 0.8rem",
            backgroundColor: "transparent",
            color: "#64748b",
            border: "1px solid #e2e8f0",
            borderRadius: "6px",
            fontSize: "0.85rem",
            cursor: "pointer",
          }}
        >
          ← 返回
        </button>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 600 }}>技术主张</h2>
        <span style={{ fontSize: "0.85rem", color: "#64748b" }}>
          {claims.length} 条主张
        </span>
      </div>

      {/* Empty state */}
      {claims.length === 0 && (
        <div style={{
          backgroundColor: "#fff",
          borderRadius: "12px",
          border: "1px solid #e2e8f0",
          padding: "3rem 2rem",
          textAlign: "center",
          color: "#64748b",
        }}>
          暂无主张 — 请先确认简历解析结果
        </div>
      )}

      {/* Filter bar */}
      {claims.length > 0 && (
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap" }}>
          <button
            onClick={() => setFilter("")}
            style={{
              ...filterPillStyle,
              backgroundColor: filter === "" ? "#0d1b2a" : "#f1f5f9",
              color: filter === "" ? "#fff" : "#64748b",
            }}
          >
            全部
          </button>
          {types.map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              style={{
                ...filterPillStyle,
                backgroundColor: filter === t ? "#0d1b2a" : "#f1f5f9",
                color: filter === t ? "#fff" : "#64748b",
              }}
            >
              {t}
            </button>
          ))}
        </div>
      )}

      {/* Claims list */}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {filtered.map((claim) => {
          const cd = claim.data as Record<string, unknown>
          const risks = (cd.risk_flags as string[]) || []
          const techs = (cd.technologies as string[]) || []
          const isExpanded = expanded === claim.claim_id

          return (
            <div key={claim.claim_id} style={cardStyle}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ flex: 1 }}>
                  {/* Claim text */}
                  <div
                    onClick={() => setExpanded(isExpanded ? null : claim.claim_id)}
                    style={{ cursor: "pointer", fontSize: "0.95rem", lineHeight: 1.5, fontWeight: 500 }}
                  >
                    {cd.claim_text as string || "(无文本)"}
                  </div>

                  {/* Badges row */}
                  <div style={{ display: "flex", gap: "0.4rem", marginTop: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
                    <span style={{ ...badge, backgroundColor: "#f0fbfa", color: "#0ea5a0" }}>
                      {(cd.claim_type as string) || "未知"}
                    </span>
                    <span style={{ ...badge, backgroundColor: "#f0fdf4", color: "#16a34a" }}>
                      优先级 {claim.priority}
                    </span>
                    <span style={{ ...badge, backgroundColor: "#fefce8", color: "#ca8a04" }}>
                      置信度 {Math.round(claim.confidence * 100)}%
                    </span>
                    {risks.map((r) => (
                      <span
                        key={r}
                        style={{ ...badge, backgroundColor: (riskColors[r] ?? "#f1f5f9") + "20", color: riskColors[r] ?? "#64748b" }}
                      >
                        {riskLabels[r] ?? r}
                      </span>
                    ))}
                  </div>

                  {/* Tech tags */}
                  {techs.length > 0 && (
                    <div style={{ display: "flex", gap: "0.3rem", marginTop: "0.4rem", flexWrap: "wrap" }}>
                      {techs.map((t) => (
                        <span key={t} style={{ fontSize: "0.75rem", color: "#64748b", backgroundColor: "#f1f5f9", padding: "0.1rem 0.4rem", borderRadius: "4px" }}>
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Enable toggle */}
                <button
                  onClick={() => toggleClaim(claim.claim_id, claim.disabled)}
                  style={{
                    padding: "0.2rem 0.6rem",
                    borderRadius: "4px",
                    border: "1px solid #e2e8f0",
                    backgroundColor: claim.disabled ? "#f1f5f9" : "#f0fdf4",
                    color: claim.disabled ? "#94a3b8" : "#16a34a",
                    fontSize: "0.75rem",
                    cursor: "pointer",
                  }}
                >
                  {claim.disabled ? "已禁用" : "启用"}
                </button>
              </div>

              {/* Expanded: verification points */}
              {isExpanded && (
                <div style={{ marginTop: "0.75rem", paddingTop: "0.75rem", borderTop: "1px solid #e2e8f0" }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.5rem" }}>验证点</div>
                  {((cd.verification_points as Array<Record<string, unknown>>) || []).length === 0 && (
                    <div style={{ fontSize: "0.8rem", color: "#94a3b8" }}>暂无验证点</div>
                  )}
                  {((cd.verification_points as Array<Record<string, unknown>>) || []).map((vp, i) => (
                    <div key={i} style={{ fontSize: "0.8rem", color: "#334155", marginBottom: "0.25rem", paddingLeft: "0.5rem" }}>
                      • {String(vp.point as string || vp.question as string || JSON.stringify(vp))}
                    </div>
                  ))}

                  {cd.expected_level != null && (
                    <div style={{ marginTop: "0.5rem", fontSize: "0.8rem", color: "#64748b" }}>
                      期望水平: <strong>{cd.expected_level as string}</strong>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

const cardStyle: React.CSSProperties = {
  backgroundColor: "#fff",
  borderRadius: "8px",
  border: "1px solid #e2e8f0",
  padding: "1rem 1.25rem",
}
const badge: React.CSSProperties = {
  padding: "0.1rem 0.4rem",
  borderRadius: "4px",
  fontSize: "0.7rem",
  fontWeight: 500,
}
const filterPillStyle: React.CSSProperties = {
  padding: "0.3rem 0.75rem",
  borderRadius: "20px",
  border: "none",
  fontSize: "0.8rem",
  cursor: "pointer",
}
