import { useState, useEffect } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { useResume, useResumeClaims, useUpdateRevision, useConfirmRevision } from "../hooks/use-resumes"
import type { ClaimItem } from "../api/resume-api"
import { ApiError } from "@/lib/api-client"

function qualityColor(score: number | null | undefined): string {
  if (score == null) return "#94a3b8"
  if (score >= 0.8) return "#22c55e"
  if (score >= 0.6) return "#f59e0b"
  return "#e63946"
}

function qualityLabel(score: number | null | undefined): string {
  if (score == null) return "--"
  if (score >= 0.8) return "优秀"
  if (score >= 0.6) return "一般"
  return "较低"
}

function qualityWarningLabel(code: string): string {
  const labels: Record<string, string> = {
    NO_BLOCKS: "没有识别到有效内容块",
    NO_TEXT_CONTENT: "没有识别到有效文本",
    PARSE_QUALITY_TOO_LOW: "解析质量较低，建议检查规范化文本",
    POSSIBLE_TWO_COLUMN_ORDER_ERROR: "检测到双栏布局，阅读顺序可能有误",
    HIGH_SYMBOL_RATIO: "特殊符号比例较高，可能存在乱码",
  }
  return labels[code] ?? code
}

export default function ResumeReviewPage() {
  const { resumeId } = useParams<{ resumeId: string }>()
  const navigate = useNavigate()
  const { data, isLoading, isError } = useResume(resumeId)
  const { data: claimsData } = useResumeClaims(resumeId)
  const updateMutation = useUpdateRevision()
  const confirmMutation = useConfirmRevision()

  const [editing, setEditing] = useState(false)
  const [editText, setEditText] = useState("")
  const [targetRole, setTargetRole] = useState("Software Engineer")
  const [dirty, setDirty] = useState(false)
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null)

  useEffect(() => {
    if (data?.normalized_text !== undefined && data.normalized_text !== null) {
      setEditText(data.normalized_text)
    }
  }, [data?.normalized_text])

  if (isLoading) {
    return <div style={{ padding: "2rem", textAlign: "center", color: "#64748b" }}>加载中...</div>
  }

  if (isError || !data) {
    return (
      <div style={{ padding: "2rem", textAlign: "center" }}>
        <p style={{ color: "#e63946" }}>加载失败或简历不存在</p>
        <button onClick={() => navigate("/app/resumes")} style={backBtnStyle}>返回列表</button>
      </div>
    )
  }

  const resolved = data

  async function handleSave() {
    if (!resolved.revision_id) return
    setMessage(null)
    try {
      await updateMutation.mutateAsync({
        resumeId: resumeId!,
        revisionId: resolved.revision_id,
        text: editText,
      })
      setEditing(false)
      setDirty(false)
      setMessage({ type: "success", text: "保存成功" })
    } catch (e) {
      setMessage({ type: "error", text: e instanceof ApiError ? e.message : "保存失败" })
    }
  }

  async function handleConfirm() {
    if (!resolved.revision_id) return
    setMessage(null)
    try {
      await confirmMutation.mutateAsync({
        resumeId: resumeId!,
        revisionId: resolved.revision_id,
        targetRole,
      })
      setMessage({ type: "success", text: "确认成功，主张已提取" })
      navigate(`/app/resumes/${resumeId}/profile`)
    } catch (e) {
      setMessage({
        type: "error",
        text: e instanceof ApiError ? e.message : "确认失败",
      })
    }
  }

  const isConfirmed = data.status === "CONFIRMED"

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
        <button onClick={() => navigate("/app/resumes")} style={backBtnStyle}>← 返回</button>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 600 }}>简历解析确认</h2>
        <span
          style={{
            padding: "0.2rem 0.6rem",
            borderRadius: "10px",
            fontSize: "0.75rem",
            fontWeight: 500,
            color: "#fff",
            backgroundColor: isConfirmed ? "#22c55e" : "#f59e0b",
          }}
        >
          {isConfirmed ? "已确认" : "待确认"}
        </span>
      </div>

      {message && (
        <div
          style={{
            padding: "0.75rem 1rem",
            borderRadius: "8px",
            marginBottom: "1rem",
            backgroundColor: message.type === "success" ? "#f0fdf4" : "#fef2f2",
            border: `1px solid ${message.type === "success" ? "#bbf7d0" : "#fecaca"}`,
            color: message.type === "success" ? "#16a34a" : "#e63946",
            fontSize: "0.9rem",
          }}
        >
          {message.text}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr 1fr", gap: "1rem" }}>
        {/* Source Preview */}
        <div style={panelStyle}>
          <h3 style={panelHeaderStyle}>原始文件</h3>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              fontSize: "0.8rem",
              lineHeight: 1.6,
              maxHeight: "60vh",
              overflow: "auto",
              color: "#334155",
            }}
          >
            {data.raw_text || "(无内容)"}
          </pre>
        </div>

        {/* Normalized Text Editor */}
        <div style={panelStyle}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
            <h3 style={panelHeaderStyle}>规范化文本</h3>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              {editing ? (
                <>
                  <button onClick={handleSave} disabled={updateMutation.isPending} style={smallPrimaryBtn}>
                    {updateMutation.isPending ? "保存中..." : "保存"}
                  </button>
                  <button
                    onClick={() => { setEditing(false); setEditText(data.normalized_text ?? ""); setDirty(false) }}
                    style={smallSecondaryBtn}
                  >
                    取消
                  </button>
                </>
              ) : (
                <button onClick={() => setEditing(true)} disabled={isConfirmed} style={smallSecondaryBtn}>
                  编辑
                </button>
              )}
            </div>
          </div>
          {editing ? (
            <textarea
              value={editText}
              onChange={(e) => { setEditText(e.target.value); setDirty(true) }}
              rows={25}
              style={{
                width: "100%",
                padding: "0.75rem",
                border: "1px solid #e2e8f0",
                borderRadius: "6px",
                resize: "vertical",
                fontSize: "0.85rem",
                lineHeight: 1.6,
                fontFamily: "inherit",
              }}
            />
          ) : (
            <pre
              style={{
                whiteSpace: "pre-wrap",
                fontSize: "0.85rem",
                lineHeight: 1.6,
                maxHeight: "60vh",
                overflow: "auto",
                color: "#334155",
              }}
            >
              {data.normalized_text || "(无内容)"}
            </pre>
          )}
        </div>

        {/* Quality Panel */}
        <div style={panelStyle}>
          <h3 style={panelHeaderStyle}>解析质量</h3>

          {/* Quality score */}
          <div style={{ textAlign: "center", margin: "1.5rem 0" }}>
            <div
              style={{
                width: 100,
                height: 100,
                borderRadius: "50%",
                backgroundColor: qualityColor(data.extraction_quality),
                color: "#fff",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto",
                fontSize: "1.5rem",
                fontWeight: 700,
              }}
            >
              {data.extraction_quality == null
                ? "--"
                : `${Math.round(data.extraction_quality * 100)}%`}
            </div>
            <div style={{ marginTop: "0.5rem", fontSize: "0.85rem", color: "#64748b" }}>
              {qualityLabel(data.extraction_quality)}
            </div>
          </div>

          {/* Warnings */}
          <div style={{ marginTop: "1rem" }}>
            <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.5rem" }}>质量说明</div>
            <ul style={{ paddingLeft: "1.2rem", fontSize: "0.8rem", color: "#64748b", lineHeight: 1.8 }}>
              <li>解析质量评分基于文本结构和完整性</li>
              <li>确认前请仔细检查规范化文本</li>
              <li>确认后将提取技术主张用于面试</li>
              {data.extraction_warnings.map((warning) => (
                <li key={warning} style={{ color: "#b45309" }}>
                  {qualityWarningLabel(warning)}
                </li>
              ))}
            </ul>
          </div>

          {/* Confirm section */}
          {!isConfirmed && (
            <div style={{ marginTop: "1.5rem", paddingTop: "1rem", borderTop: "1px solid #e2e8f0" }}>
              <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 500, marginBottom: "0.25rem" }}>
                目标岗位
              </label>
              <input
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder="例如：Software Engineer"
                style={{
                  width: "100%",
                  padding: "0.5rem 0.75rem",
                  border: "1px solid #e2e8f0",
                  borderRadius: "6px",
                  fontSize: "0.9rem",
                  marginBottom: "0.75rem",
                }}
              />
              <button
                onClick={handleConfirm}
                disabled={confirmMutation.isPending}
                style={{
                  width: "100%",
                  padding: "0.6rem 1.5rem",
                  backgroundColor: confirmMutation.isPending ? "#cbd5e1" : "#22c55e",
                  color: "#fff",
                  border: "none",
                  borderRadius: "6px",
                  fontSize: "0.9rem",
                  fontWeight: 500,
                }}
              >
                {confirmMutation.isPending ? "确认中..." : "确认并提取主张"}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Structured profile data (shown when confirmed) */}
      {isConfirmed && (
        <ProfileSection resumeId={resumeId!} profile={data.profile as Record<string, unknown> | null} claims={claimsData?.claims ?? []} />
      )}

      {/* Dirty state warning */}
      {dirty && (
        <div
          style={{
            position: "fixed",
            bottom: "1rem",
            left: "50%",
            transform: "translateX(-50%)",
            padding: "0.75rem 1.5rem",
            backgroundColor: "#0d1b2a",
            color: "#fff",
            borderRadius: "8px",
            fontSize: "0.85rem",
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
          }}
        >
          有未保存的修改
        </div>
      )}
    </div>
  )
}

function ProfileSection({ resumeId, profile, claims }: { resumeId: string; profile: Record<string, unknown> | null; claims: ClaimItem[] }) {
  if (!profile) {
    return (
      <div style={{ marginTop: "1rem", padding: "1.5rem", backgroundColor: "#fff", borderRadius: "12px", border: "1px solid #e2e8f0", textAlign: "center" }}>
        <p style={{ color: "#94a3b8", fontSize: "0.9rem" }}>暂无结构化数据，请确认简历后查看</p>
      </div>
    )
  }

  const summary = profile.summary as string | undefined
  const projects = (profile.projects as Array<Record<string, unknown>>) || []
  const experiences = (profile.experiences as Array<Record<string, unknown>>) || []
  const skills = (profile.skills as string[]) || []
  const education = (profile.education as Array<Record<string, unknown>>) || []

  return (
    <div style={{ marginTop: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
      <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#1e293b" }}>简历分析结果</h3>

      {/* Summary */}
      {summary && (
        <div style={profileCardStyle}>
          <h4 style={profileSectionTitle}>总览</h4>
          <p style={{ fontSize: "0.9rem", lineHeight: 1.7, color: "#334155", whiteSpace: "pre-wrap" }}>{summary}</p>
        </div>
      )}

      {/* Projects / Entries */}
      {projects.length > 0 && (
        <div style={profileCardStyle}>
          <h4 style={profileSectionTitle}>项目经历 ({projects.length})</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {projects.map((entry, i) => {
              const title = (entry.title as string) || (entry.role as string) || `项目 ${i + 1}`
              const desc = (entry.summary as string) || ""
              const highlights = (entry.bullets as string[]) || []
              return (
                <CollapsibleCard key={i} title={title}>
                  {desc && (
                    <p style={{ fontSize: "0.85rem", lineHeight: 1.6, color: "#64748b", whiteSpace: "pre-wrap", marginBottom: highlights.length > 0 ? "0.5rem" : 0 }}>
                      {desc}
                    </p>
                  )}
                  {highlights.length > 0 && (
                    <ul style={{ paddingLeft: "1.25rem", fontSize: "0.85rem", lineHeight: 1.6, color: "#334155", margin: 0 }}>
                      {highlights.map((h, j) => (<li key={j}>{h}</li>))}
                    </ul>
                  )}
                </CollapsibleCard>
              )
            })}
          </div>
        </div>
      )}

      {experiences.length > 0 && (
        <div style={profileCardStyle}>
          <h4 style={profileSectionTitle}>工作经历 ({experiences.length})</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {experiences.map((entry, i) => (
              <CollapsibleCard
                key={i}
                title={`${(entry.organization as string) || "公司"} — ${(entry.role as string) || (entry.title as string) || "职位"}`}
              >
                {(entry.summary as string) && (
                  <p style={{ fontSize: "0.85rem", lineHeight: 1.6, color: "#64748b" }}>{entry.summary as string}</p>
                )}
                {((entry.bullets as string[]) || []).length > 0 && (
                  <ul style={{ paddingLeft: "1.25rem", fontSize: "0.85rem", lineHeight: 1.6, color: "#334155" }}>
                    {(entry.bullets as string[]).map((item, index) => <li key={index}>{item}</li>)}
                  </ul>
                )}
              </CollapsibleCard>
            ))}
          </div>
        </div>
      )}

      {/* Skills */}
      {skills.length > 0 && (
        <div style={profileCardStyle}>
          <h4 style={profileSectionTitle}>技能标签</h4>
          <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
            {skills.map((s) => (
              <span key={s} style={skillTagStyle}>{s}</span>
            ))}
          </div>
        </div>
      )}

      {/* Education */}
      {education.length > 0 && (
        <div style={profileCardStyle}>
          <h4 style={profileSectionTitle}>教育背景</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
            {education.map((edu, i) => (
              <div key={i} style={{ fontSize: "0.85rem", color: "#334155" }}>
                <span style={{ fontWeight: 500 }}>{(edu.organization as string) || (edu.title as string)}</span>
                {(edu.role as string) && <span> — {edu.role as string}</span>}
                {(edu.title as string) && edu.title !== edu.organization && <span>，{edu.title as string}</span>}
                {((edu.date_range as Record<string, unknown> | undefined)?.raw as string) && (
                  <span style={{ color: "#94a3b8" }}> · {(edu.date_range as Record<string, unknown>).raw as string}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Claims */}
      <div style={profileCardStyle}>
        <h4 style={profileSectionTitle}>主张与验证点</h4>
        {claims.length === 0 ? (
          <p style={{ color: "#94a3b8", fontSize: "0.85rem" }}>暂无主张数据</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
            {claims.slice(0, 8).map((claim) => {
              const cd = (claim.data ?? {}) as Record<string, unknown>
              return (
                <div key={claim.claim_id} style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem" }}>
                  <span style={{
                    width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
                    backgroundColor: claim.priority >= 8 ? "#e63946" : claim.priority >= 5 ? "#f59e0b" : "#94a3b8",
                  }} />
                  <span style={{ color: "#334155", flex: 1 }}>
                    {(cd.claim_text as string) || `Claim ${claim.claim_id.slice(0, 8)}`}
                  </span>
                  <span style={{ fontSize: "0.7rem", color: "#94a3b8" }}>
                    P{claim.priority}
                  </span>
                </div>
              )
            })}
          </div>
        )}
        <div style={{ marginTop: "0.75rem" }}>
          <Link to={`/app/resumes/${resumeId}/claims`} style={{ fontSize: "0.8rem", color: "#0ea5a0", textDecoration: "none" }}>
            查看全部 ({claims.length}) →
          </Link>
        </div>
      </div>
    </div>
  )
}

function CollapsibleCard({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ border: "1px solid #e2e8f0", borderRadius: "8px", overflow: "hidden" }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: "100%", padding: "0.6rem 0.75rem", backgroundColor: open ? "#f8fafc" : "#fff",
          border: "none", textAlign: "left", fontSize: "0.85rem", fontWeight: 500,
          color: "#334155", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center",
        }}
      >
        <span>{title}</span>
        <span style={{ color: "#94a3b8", fontSize: "0.75rem" }}>{open ? "收起" : "展开"}</span>
      </button>
      {open && <div style={{ padding: "0.65rem 0.75rem", borderTop: "1px solid #e2e8f0" }}>{children}</div>}
    </div>
  )
}

const panelStyle: React.CSSProperties = {
  backgroundColor: "#fff",
  borderRadius: "8px",
  border: "1px solid #e2e8f0",
  padding: "1rem",
}
const profileCardStyle: React.CSSProperties = {
  backgroundColor: "#fff",
  borderRadius: "12px",
  border: "1px solid #e2e8f0",
  padding: "1.25rem",
}
const profileSectionTitle: React.CSSProperties = {
  fontSize: "0.85rem",
  fontWeight: 600,
  color: "#64748b",
  marginBottom: "0.65rem",
}
const skillTagStyle: React.CSSProperties = {
  padding: "0.2rem 0.55rem",
  backgroundColor: "#f0fbfa",
  color: "#0ea5a0",
  borderRadius: "6px",
  fontSize: "0.8rem",
  fontWeight: 500,
}
const panelHeaderStyle: React.CSSProperties = {
  fontSize: "0.85rem",
  fontWeight: 600,
  color: "#64748b",
  margin: 0,
}
const backBtnStyle: React.CSSProperties = {
  padding: "0.4rem 0.8rem",
  backgroundColor: "transparent",
  color: "#64748b",
  border: "1px solid #e2e8f0",
  borderRadius: "6px",
  fontSize: "0.85rem",
  cursor: "pointer",
}
const smallPrimaryBtn: React.CSSProperties = {
  padding: "0.3rem 0.75rem",
  backgroundColor: "#0d1b2a",
  color: "#fff",
  border: "none",
  borderRadius: "4px",
  fontSize: "0.8rem",
}
const smallSecondaryBtn: React.CSSProperties = {
  padding: "0.3rem 0.75rem",
  backgroundColor: "transparent",
  color: "#64748b",
  border: "1px solid #e2e8f0",
  borderRadius: "4px",
  fontSize: "0.8rem",
}
