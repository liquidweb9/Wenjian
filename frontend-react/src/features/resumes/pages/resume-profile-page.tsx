import { useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { FileText } from "lucide-react"
import { useResume, useResumeClaims } from "../hooks/use-resumes"
import { EmptyState } from "@/components/common/empty-state"
import { LoadingState } from "@/components/common/loading-state"
import { PageHeader } from "@/components/common/page-header"
import { usePageTitle } from "@/lib/use-page-title"

export default function ResumeProfilePage() {
  const { resumeId } = useParams<{ resumeId: string }>()
  const navigate = useNavigate()
  usePageTitle("", "简历画像")

  const { data, isLoading } = useResume(resumeId)
  const { data: claimsData } = useResumeClaims(resumeId)

  if (isLoading) {
    return <LoadingState message="问鉴正在整理这份简历的结构化画像与证据。" />
  }

  if (!data) {
    return (
      <EmptyState
        title="这份简历暂时不可用"
        description="你访问的简历不存在，或当前还没有可展示的结构化内容。"
        action={
          <button type="button" className="btn-primary" onClick={() => navigate("/app/resumes")}>
            返回简历管理
          </button>
        }
      />
    )
  }

  const profile = data.profile as Record<string, unknown> | null
  const claims = claimsData?.claims ?? []
  const summary = profile?.summary as string | undefined
  const projects = (profile?.projects as Array<Record<string, unknown>>) || []
  const skills = (profile?.skills as string[]) || []
  const education = (profile?.education as Array<Record<string, unknown>>) || []
  const experiences = (profile?.experiences as Array<Record<string, unknown>>) || []

  return (
    <div>
      <PageHeader
        title="简历画像"
        description="以文档式视角查看这份简历的结构化经历、技能与主张证据，决定下一轮面试如何发问。"
        brand
        back={{ to: `/app/resumes/${resumeId}/review`, label: "返回简历审阅" }}
      />

      <section className="app-surface" style={{ padding: "1.3rem 1.4rem", marginBottom: "1rem" }}>
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) auto", gap: "1rem" }}>
          <div>
            <div className="app-eyebrow">Resume Overview</div>
            <div style={{ marginTop: "0.4rem", fontSize: "1.2rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
              {data.file_name}
            </div>
            <p style={{ margin: "0.55rem 0 0", color: "var(--wj-text-secondary)", lineHeight: 1.7 }}>
              当前状态：{data.status}。问鉴会依据这份资料中的教育、工作、项目和技能经历生成可追问的问题与证据校验。
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.65rem", alignItems: "flex-start", flexWrap: "wrap", justifyContent: "flex-end" }}>
            <Link to={`/app/resumes/${resumeId}/claims`} className="btn-secondary">
              查看主张证据
            </Link>
            {data.status === "CONFIRMED" ? (
              <Link to={`/app/interviews/new?resume_id=${resumeId}`} className="btn-primary">
                基于此简历创建面试
              </Link>
            ) : null}
          </div>
        </div>
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "1.35fr 0.65fr", gap: "1rem", alignItems: "start" }}>
        <div style={{ display: "grid", gap: "1rem" }}>
          {summary ? (
            <DocumentSection title="基本信息摘要">
              <p style={paragraphStyle}>{summary}</p>
            </DocumentSection>
          ) : null}

          {experiences.length > 0 ? (
            <DocumentSection title="工作经历">
              <div style={{ display: "grid", gap: "0.8rem" }}>
                {experiences.map((experience, index) => (
                  <CollapsibleDoc
                    key={`${experience.organization as string}-${index}`}
                    title={`${(experience.organization as string) || "工作经历"} · ${(experience.role as string) || (experience.title as string) || "岗位"}`}
                  >
                    {(experience.summary as string) ? <p style={paragraphStyle}>{experience.summary as string}</p> : null}
                    {((experience.bullets as string[]) || []).length ? (
                      <ul style={listStyle}>
                        {(experience.bullets as string[]).map((item, itemIndex) => (
                          <li key={itemIndex}>{item}</li>
                        ))}
                      </ul>
                    ) : null}
                  </CollapsibleDoc>
                ))}
              </div>
            </DocumentSection>
          ) : null}

          {projects.length > 0 ? (
            <DocumentSection title="项目经历">
              <div style={{ display: "grid", gap: "0.8rem" }}>
                {projects.map((project, index) => (
                  <CollapsibleDoc
                    key={`${project.title as string}-${index}`}
                    title={(project.title as string) || (project.role as string) || `项目 ${index + 1}`}
                  >
                    {(project.summary as string) ? <p style={paragraphStyle}>{project.summary as string}</p> : null}
                    {((project.bullets as string[]) || []).length ? (
                      <ul style={listStyle}>
                        {(project.bullets as string[]).map((item, itemIndex) => (
                          <li key={itemIndex}>{item}</li>
                        ))}
                      </ul>
                    ) : null}
                  </CollapsibleDoc>
                ))}
              </div>
            </DocumentSection>
          ) : null}

          {!summary && !experiences.length && !projects.length ? (
            <DocumentSection title="原始内容">
              <pre
                style={{
                  margin: 0,
                  padding: "1rem",
                  borderRadius: 14,
                  background: "var(--wj-bg-surface-secondary)",
                  border: "1px solid var(--wj-border-subtle)",
                  color: "var(--wj-text-secondary)",
                  whiteSpace: "pre-wrap",
                }}
              >
                {data.normalized_text || data.raw_text || "暂无可展示内容"}
              </pre>
            </DocumentSection>
          ) : null}
        </div>

        <div style={{ display: "grid", gap: "1rem" }}>
          <DocumentSection title="技能">
            {skills.length ? (
              <div style={{ display: "flex", gap: "0.45rem", flexWrap: "wrap" }}>
                {skills.map((skill) => (
                  <span
                    key={skill}
                    style={{
                      padding: "0.3rem 0.7rem",
                      borderRadius: 999,
                      background: "var(--wj-brand-accent-bg)",
                      color: "var(--wj-brand-secondary)",
                      fontSize: "0.82rem",
                      fontWeight: 600,
                    }}
                  >
                    {skill}
                  </span>
                ))}
              </div>
            ) : (
              <p style={paragraphStyle}>暂无结构化技能信息。</p>
            )}
          </DocumentSection>

          <DocumentSection title="教育经历">
            {education.length ? (
              <div style={{ display: "grid", gap: "0.75rem" }}>
                {education.map((item, index) => (
                  <div key={index} className="app-muted-surface" style={{ padding: "0.9rem 1rem" }}>
                    <div style={{ fontWeight: 600, color: "var(--wj-text-primary)" }}>
                      {(item.organization as string) || (item.title as string) || "教育经历"}
                    </div>
                    <div style={{ marginTop: "0.3rem", color: "var(--wj-text-secondary)", fontSize: "0.84rem", lineHeight: 1.6 }}>
                      {(item.role as string) || ""}
                      {(item.title as string) && item.title !== item.organization ? ` · ${item.title as string}` : ""}
                      {((item.date_range as Record<string, unknown> | undefined)?.raw as string)
                        ? ` · ${(item.date_range as Record<string, unknown>).raw as string}`
                        : ""}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={paragraphStyle}>暂无结构化教育信息。</p>
            )}
          </DocumentSection>

          <DocumentSection title="ResumeClaim 与证据">
            {claims.length ? (
              <div style={{ display: "grid", gap: "0.65rem" }}>
                {claims
                  .sort((a, b) => b.priority - a.priority)
                  .slice(0, 8)
                  .map((claim) => {
                    const claimData = claim.data as Record<string, unknown>
                    return (
                      <div key={claim.claim_id} className="app-muted-surface" style={{ padding: "0.9rem 1rem" }}>
                        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "0.4rem" }}>
                          <Tag text={`优先级 ${claim.priority}`} tone="warning" />
                          <Tag text={`${Math.round(claim.confidence * 100)}% 置信度`} tone="success" />
                          <Tag text={(claimData.claim_type as string) || "CLAIM"} tone="default" />
                        </div>
                        <div style={{ color: "var(--wj-text-primary)", fontSize: "0.88rem", lineHeight: 1.65 }}>
                          {(claimData.claim_text as string) || "暂无主张文本"}
                        </div>
                      </div>
                    )
                  })}
              </div>
            ) : (
              <p style={paragraphStyle}>当前还没有结构化主张证据。</p>
            )}
          </DocumentSection>
        </div>
      </div>
    </div>
  )
}

function DocumentSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="app-surface" style={{ padding: "1.2rem 1.25rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.55rem", marginBottom: "0.85rem" }}>
        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: 12,
            background: "var(--wj-brand-accent-bg)",
            color: "var(--wj-brand-secondary)",
            display: "grid",
            placeItems: "center",
          }}
        >
          <FileText size={16} />
        </div>
        <h2 style={{ margin: 0, fontSize: "1.02rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>{title}</h2>
      </div>
      {children}
    </section>
  )
}

function CollapsibleDoc({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(true)

  return (
    <div className="app-muted-surface" style={{ overflow: "hidden" }}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        style={{
          width: "100%",
          border: "none",
          background: "transparent",
          textAlign: "left",
          padding: "0.9rem 1rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          color: "var(--wj-text-primary)",
          fontWeight: 600,
        }}
      >
        <span>{title}</span>
        <span style={{ color: "var(--wj-text-secondary)", fontSize: "0.82rem" }}>{open ? "收起" : "展开"}</span>
      </button>
      {open ? <div style={{ padding: "0 1rem 1rem" }}>{children}</div> : null}
    </div>
  )
}

function Tag({ text, tone }: { text: string; tone: "default" | "warning" | "success" }) {
  const colors =
    tone === "warning"
      ? { bg: "#fffbeb", text: "#b45309" }
      : tone === "success"
        ? { bg: "#f0fdf4", text: "#166534" }
        : { bg: "#f1f5f9", text: "#475569" }

  return (
    <span style={{ padding: "0.2rem 0.55rem", borderRadius: 999, background: colors.bg, color: colors.text, fontSize: "0.76rem", fontWeight: 600 }}>
      {text}
    </span>
  )
}

const paragraphStyle: React.CSSProperties = {
  margin: 0,
  color: "var(--wj-text-secondary)",
  lineHeight: 1.75,
  fontSize: "0.9rem",
}

const listStyle: React.CSSProperties = {
  margin: "0.6rem 0 0",
  paddingLeft: "1.2rem",
  color: "var(--wj-text-secondary)",
  lineHeight: 1.7,
  fontSize: "0.9rem",
}
