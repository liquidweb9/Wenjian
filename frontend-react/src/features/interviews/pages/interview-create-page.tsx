import { useEffect, useMemo, useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { CheckCircle2, ChevronRight, ClipboardList, FileText, Target } from "lucide-react"
import { useResumeList } from "@/features/resumes/hooks/use-resumes"
import { useJobTargets } from "@/features/job-target/hooks/use-job-targets"
import { useCreateInterview } from "../hooks/use-interviews"
import { usePreferenceStore } from "@/stores/preference-store"
import { EmptyState } from "@/components/common/empty-state"
import { PageHeader } from "@/components/common/page-header"
import { usePageTitle } from "@/lib/use-page-title"

const steps = [
  "选择简历",
  "选择岗位目标（可选）",
  "设置目标岗位名称",
  "设置面试模式与轮次",
  "补充岗位描述（可选）",
  "开始模拟面试",
]

export default function InterviewCreatePage() {
  usePageTitle("/app/interviews/new")
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const preselectResumeId = searchParams.get("resume_id") || ""
  const createInterview = useCreateInterview()
  const preferences = usePreferenceStore()

  const [resumeId, setResumeId] = useState(preselectResumeId)
  const [revisionId, setRevisionId] = useState<string | null>(null)
  const [jobTargetId, setJobTargetId] = useState<string>("")
  const [targetRole, setTargetRole] = useState("")
  const [jobDescription, setJobDescription] = useState("")
  const [mode, setMode] = useState(preferences.defaultMode)
  const [maxTurns, setMaxTurns] = useState(preferences.defaultMaxTurns)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const { data: resumesData, isLoading: resumesLoading } = useResumeList({
    status: "CONFIRMED",
    page_size: 50,
  })
  const { data: jobTargets } = useJobTargets()

  const confirmedResumes = useMemo(() => resumesData?.items ?? [], [resumesData])

  useEffect(() => {
    if (preselectResumeId && confirmedResumes.length > 0) {
      const selected = confirmedResumes.find((resume) => resume.resume_id === preselectResumeId)
      if (selected?.latest_revision_id) {
        setRevisionId(selected.latest_revision_id)
      }
    }
  }, [preselectResumeId, confirmedResumes])

  function validate() {
    const nextErrors: Record<string, string> = {}
    if (!resumeId) nextErrors.resumeId = "请选择一份已确认的简历。"
    if (!revisionId) nextErrors.resumeId = "所选简历缺少可用版本。"
    if (!targetRole.trim()) nextErrors.targetRole = "请输入目标岗位。"
    if (maxTurns < 3 || maxTurns > 30) nextErrors.maxTurns = "轮次需保持在 3 到 30 之间。"
    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  function handleResumeChange(nextResumeId: string) {
    setResumeId(nextResumeId)
    const selected = confirmedResumes.find((resume) => resume.resume_id === nextResumeId)
    setRevisionId(selected?.latest_revision_id ?? null)
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!validate()) return

    await createInterview.mutateAsync({
      resume_id: resumeId,
      resume_revision_id: revisionId!,
      target_role: targetRole.trim(),
      job_description: jobDescription.trim() || undefined,
      job_target_id: jobTargetId || undefined,
      mode,
      max_turns: maxTurns,
    })
  }

  return (
    <div>
      <PageHeader
        title="创建模拟面试"
        description="问鉴会根据你的简历、目标岗位和考察方向生成个性化面试计划。页面重点是配置真实训练输入，而不是展示空洞的宣传文案。"
        brand
      />

      <div style={{ display: "grid", gridTemplateColumns: "0.7fr 1.3fr", gap: "1rem", alignItems: "start" }}>
        <section className="app-surface" style={{ padding: "1.2rem 1.25rem" }}>
          <div className="app-eyebrow">Interview Flow</div>
          <h2 style={{ margin: "0.45rem 0 0", fontSize: "1.12rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
            创建流程
          </h2>
          <div style={{ display: "grid", gap: "0.7rem", marginTop: "1rem" }}>
            {steps.map((step, index) => (
              <div key={step} className="app-muted-surface" style={{ padding: "0.8rem 0.9rem", display: "flex", gap: "0.7rem", alignItems: "center" }}>
                <div
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 999,
                    background: index < 4 ? "var(--wj-brand-accent-bg)" : "var(--wj-bg-surface)",
                    color: index < 4 ? "var(--wj-brand-secondary)" : "var(--wj-text-secondary)",
                    display: "grid",
                    placeItems: "center",
                    fontSize: "0.76rem",
                    fontWeight: 700,
                    border: "1px solid var(--wj-border-default)",
                  }}
                >
                  {index + 1}
                </div>
                <span style={{ color: "var(--wj-text-primary)", fontSize: "0.88rem", fontWeight: 500 }}>{step}</span>
              </div>
            ))}
          </div>
        </section>

        <form onSubmit={handleSubmit} className="app-surface" style={{ padding: "1.3rem 1.4rem" }}>
          {resumesLoading ? (
            <p style={{ color: "var(--wj-text-secondary)" }}>问鉴正在读取可用于面试的已确认简历…</p>
          ) : confirmedResumes.length === 0 ? (
            <EmptyState
              title="当前还没有可用的已确认简历"
              description="先完成简历上传与确认，再回到这里创建模拟面试。这样问鉴才能基于真实经历生成连续追问。"
              action={
                <button type="button" className="btn-primary" onClick={() => navigate("/app/resumes/new")}>
                  去上传简历
                </button>
              }
            />
          ) : (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                <Field label="1. 选择简历" description="只展示已确认、可直接用于面试的问题来源。">
                  <select value={resumeId} onChange={(event) => handleResumeChange(event.target.value)} style={fieldInputStyle(errors.resumeId)}>
                    <option value="">请选择一份简历</option>
                    {confirmedResumes.map((resume) => (
                      <option key={resume.resume_id} value={resume.resume_id}>
                        {resume.file_name}
                      </option>
                    ))}
                  </select>
                  {errors.resumeId ? <FieldError>{errors.resumeId}</FieldError> : null}
                </Field>

                <Field label="2. 岗位目标（可选）" description="选择已创建的岗位目标，系统将优先考察该岗位的能力缺口。">
                  <select value={jobTargetId} onChange={(event) => setJobTargetId(event.target.value)} style={fieldInputStyle()}>
                    <option value="">不选择岗位目标</option>
                    {(jobTargets || []).map((jobTarget) => (
                      <option key={jobTarget.job_target_id} value={jobTarget.job_target_id}>
                        {jobTarget.title}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1rem" }}>
                <Field label="3. 目标岗位名称" description="这会影响提问范围、深度和反馈角度。">
                  <input
                    type="text"
                    value={targetRole}
                    onChange={(event) => setTargetRole(event.target.value)}
                    placeholder="例如：高级后端工程师"
                    style={fieldInputStyle(errors.targetRole)}
                  />
                  {errors.targetRole ? <FieldError>{errors.targetRole}</FieldError> : null}
                </Field>

                <Field label="4. 面试模式" description="练习模式更轻量，模拟面试更接近真实流程。">
                  <div style={{ display: "grid", gap: "0.7rem" }}>
                    <ModeOption
                      active={mode === "simulation"}
                      title="模拟面试"
                      description="强调完整追问、评分与反馈。"
                      onClick={() => setMode("simulation")}
                    />
                    <ModeOption
                      active={mode === "practice"}
                      title="练习模式"
                      description="适合先快速热身，再进入正式训练。"
                      onClick={() => setMode("practice")}
                    />
                  </div>
                </Field>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1rem" }}>
                <Field
                  label="5. 最大轮次"
                  description="15 轮只是默认值，可设置 3–30 轮。系统会根据证据是否充分、回答深度与项目覆盖度决定继续追问或切换项目，也可能提前结束。"
                >
                  <input
                    type="number"
                    min={3}
                    max={30}
                    value={maxTurns}
                    onChange={(event) => setMaxTurns(Number(event.target.value))}
                    style={fieldInputStyle(errors.maxTurns)}
                  />
                  {errors.maxTurns ? <FieldError>{errors.maxTurns}</FieldError> : null}
                  <div className="turn-presets" aria-label="推荐面试轮次">
                    {[10, 15, 20, 25, 30].map((turns) => (
                      <button
                        key={turns}
                        type="button"
                        className={maxTurns === turns ? "turn-preset is-active" : "turn-preset"}
                        onClick={() => setMaxTurns(turns)}
                      >
                        {turns} 轮
                      </button>
                    ))}
                  </div>
                </Field>
              </div>

              <Field label="6. 岗位描述（可选）" description="补充 JD 后，问鉴会更容易聚焦岗位背景、技术栈和职责重点。">
                <textarea
                  value={jobDescription}
                  onChange={(event) => setJobDescription(event.target.value)}
                  placeholder="粘贴目标岗位的 JD，帮助问鉴生成更贴近岗位预期的问题。"
                  rows={6}
                  style={{ ...fieldInputStyle(), resize: "vertical", minHeight: 144 }}
                />
              </Field>

              <section className="app-muted-surface" style={{ marginTop: "1rem", padding: "1rem" }}>
                <div className="app-eyebrow">InterviewPlan Preview</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "0.75rem", marginTop: "0.75rem" }}>
                  <PreviewItem icon={FileText} label="简历来源" value={resumeId ? "已选择" : "待选择"} />
                  <PreviewItem icon={Target} label="岗位目标" value={jobTargetId ? "已选择" : "未选择"} />
                  <PreviewItem icon={ClipboardList} label="计划轮次" value={`${maxTurns} 轮`} />
                </div>
              </section>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1.25rem", gap: "1rem" }}>
                <button type="button" className="btn-secondary" onClick={() => navigate("/app/interviews")}>
                  返回面试记录
                </button>
                <div style={{ display: "grid", justifyItems: "end", gap: "0.45rem" }}>
                  <button type="submit" className="btn-primary" disabled={createInterview.isPending}>
                    {createInterview.isPending ? "正在创建面试…" : "确认并开始面试"}
                    <ChevronRight size={16} />
                  </button>
                  {createInterview.isError ? (
                    <span style={{ color: "var(--wj-error)", fontSize: "0.8rem" }}>
                      {(createInterview.error as Error)?.message || "创建失败，请稍后重试。"}
                    </span>
                  ) : null}
                </div>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  )
}

function Field({
  label,
  description,
  children,
}: {
  label: string
  description: string
  children: React.ReactNode
}) {
  return (
    <div style={{ marginTop: "1rem" }}>
      <label style={{ display: "block", marginBottom: "0.5rem", color: "var(--wj-text-primary)", fontWeight: 600 }}>{label}</label>
      <p style={{ margin: "0 0 0.7rem", color: "var(--wj-text-secondary)", fontSize: "0.82rem", lineHeight: 1.6 }}>{description}</p>
      {children}
    </div>
  )
}

function ModeOption({
  active,
  title,
  description,
  onClick,
}: {
  active: boolean
  title: string
  description: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        borderRadius: 14,
        border: active ? "1px solid rgba(14,149,144,0.42)" : "1px solid var(--wj-border-default)",
        background: active ? "var(--wj-brand-accent-bg)" : "var(--wj-bg-surface)",
        padding: "0.9rem 1rem",
        textAlign: "left",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: "0.8rem" }}>
        <div>
          <div style={{ color: "var(--wj-text-primary)", fontWeight: 600 }}>{title}</div>
          <div style={{ marginTop: "0.3rem", color: "var(--wj-text-secondary)", fontSize: "0.82rem", lineHeight: 1.6 }}>{description}</div>
        </div>
        {active ? <CheckCircle2 size={18} color="var(--wj-brand-secondary)" /> : null}
      </div>
    </button>
  )
}

function PreviewItem({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof FileText
  label: string
  value: string
}) {
  return (
    <div style={{ display: "grid", gap: "0.25rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.45rem", color: "var(--wj-text-tertiary)", fontSize: "0.76rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        <Icon size={14} />
        {label}
      </div>
      <div style={{ color: "var(--wj-text-primary)", fontWeight: 600 }}>{value}</div>
    </div>
  )
}

function FieldError({ children }: { children: React.ReactNode }) {
  return <div style={{ marginTop: "0.45rem", color: "var(--wj-error)", fontSize: "0.78rem" }}>{children}</div>
}

function fieldInputStyle(error?: string): React.CSSProperties {
  return {
    width: "100%",
    minHeight: 48,
    padding: "0.75rem 0.9rem",
    borderRadius: 12,
    border: error ? "1px solid var(--wj-error)" : "1px solid var(--wj-border-default)",
    background: "var(--wj-bg-surface)",
    color: "var(--wj-text-primary)",
  }
}
