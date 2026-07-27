import { Link, useNavigate } from "react-router-dom"
import { ArrowRight, BarChart3, ClipboardList, FileText, MessageSquare } from "lucide-react"
import { WelcomePanel } from "@/components/common/welcome-panel"
import { EmptyState } from "@/components/common/empty-state"
import { LoadingState } from "@/components/common/loading-state"
import { useDashboardSummary } from "../hooks/use-dashboard"
import { usePageTitle } from "@/lib/use-page-title"

export default function DashboardPage() {
  usePageTitle("/app/dashboard")
  const navigate = useNavigate()
  const { data, isLoading } = useDashboardSummary()

  if (isLoading) {
    return (
      <div>
        <WelcomePanel />
        <LoadingState message="问鉴正在整理你的简历、面试和报告概况。" />
      </div>
    )
  }

  const totalResumes = data?.total_resumes ?? 0
  const totalInterviews = data?.total_interviews ?? 0
  const averageScore = data?.average_score ?? 0
  const pendingReviews = data?.pending_reviews ?? 0
  const prepProgress = totalInterviews > 0 ? Math.min(100, Math.round((averageScore / 100) * 65 + Math.min(totalResumes, 4) * 8)) : Math.min(40, totalResumes * 10)

  return (
    <div>
      <WelcomePanel />

      <div style={{ display: "grid", gridTemplateColumns: "1.3fr 0.7fr", gap: "1.25rem", marginBottom: "1.5rem" }}>
        <section className="app-surface" style={{ padding: "1.35rem 1.4rem" }}>
          <div className="app-eyebrow">Next Actions</div>
          <h2 style={{ margin: "0.45rem 0 0", fontSize: "1.28rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
            从当前业务状态继续，不从零开始
          </h2>
          <p style={{ margin: "0.55rem 0 0", color: "var(--wj-text-secondary)", lineHeight: 1.7 }}>
            优先回到未完成的模拟面试，其次补齐待确认简历，再开始新的岗位训练。
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "0.85rem", marginTop: "1.25rem" }}>
            <ActionCard
              icon={MessageSquare}
              title="继续模拟面试"
              description="延续上下文完成追问与评分"
              to="/app/interviews"
              primary
            />
            <ActionCard
              icon={FileText}
              title="上传新简历"
              description="新增简历并进入解析确认流程"
              to="/app/resumes/new"
            />
            <ActionCard
              icon={ClipboardList}
              title="查看简历管理"
              description="处理待确认资料，准备下一轮面试"
              to="/app/resumes"
            />
          </div>
        </section>

        <section className="app-surface" style={{ padding: "1.35rem 1.4rem" }}>
          <div className="app-eyebrow">Preparation Progress</div>
          <h2 style={{ margin: "0.45rem 0 0", fontSize: "1.22rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
            面试准备进度
          </h2>
          <div style={{ marginTop: "1.1rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <span style={{ fontSize: "2rem", fontWeight: 700, color: "var(--wj-text-primary)" }}>{prepProgress}%</span>
              <span style={{ color: "var(--wj-text-secondary)", fontSize: "0.82rem" }}>基于当前简历和面试数据估算</span>
            </div>
            <div style={{ marginTop: "0.75rem", height: 10, borderRadius: 999, background: "var(--wj-bg-subtle)", overflow: "hidden" }}>
              <div
                style={{
                  width: `${prepProgress}%`,
                  height: "100%",
                  borderRadius: 999,
                  background: "linear-gradient(90deg, var(--wj-brand-secondary) 0%, var(--wj-brand-accent) 100%)",
                }}
              />
            </div>
            <p style={{ margin: "0.85rem 0 0", color: "var(--wj-text-secondary)", fontSize: "0.86rem", lineHeight: 1.7 }}>
              继续完成未结束面试，会帮助问鉴更完整地分析回答质量与证据一致性。
            </p>
          </div>
        </section>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "0.95fr 1.05fr", gap: "1.25rem", marginBottom: "1.5rem" }}>
        <section className="app-surface" style={{ padding: "1.35rem 1.4rem" }}>
          <SectionHeading title="真实业务统计" caption="只显示当前系统确有的数据" icon={BarChart3} />
          <div style={{ display: "grid", gap: "0.8rem", marginTop: "1.1rem" }}>
            <MetricRow label="已上传简历" value={String(totalResumes)} hint="包含可继续用于面试的资料" />
            <MetricRow label="累计面试" value={String(totalInterviews)} hint="历史训练总次数" />
            <MetricRow label="平均得分" value={totalInterviews > 0 ? `${averageScore} / 100` : "--"} hint="基于已完成题目评分" />
            <MetricRow label="待处理简历" value={String(pendingReviews)} hint="建议优先确认后再创建面试" />
          </div>
        </section>

        <section className="app-surface" style={{ padding: "1.35rem 1.4rem" }}>
          <SectionHeading title="进行中的模拟面试" caption="优先恢复上下文连续的训练过程" icon={MessageSquare} />
          {data?.in_progress_interviews.length ? (
            <div style={{ display: "grid", gap: "0.8rem", marginTop: "1.1rem" }}>
              {data.in_progress_interviews.map((item) => (
                <button
                  key={item.interview_id}
                  type="button"
                  onClick={() => navigate(`/app/interviews/${item.interview_id}/live`)}
                  style={{
                    textAlign: "left",
                    border: "1px solid var(--wj-border-default)",
                    borderRadius: 14,
                    background: "var(--wj-bg-surface)",
                    padding: "1rem",
                    display: "grid",
                    gap: "0.45rem",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "center" }}>
                    <span style={{ fontSize: "0.98rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
                      {item.target_role || "未指定目标岗位"}
                    </span>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        padding: "0.2rem 0.55rem",
                        borderRadius: 999,
                        background: "var(--wj-brand-accent-bg)",
                        color: "var(--wj-brand-secondary)",
                        fontSize: "0.76rem",
                        fontWeight: 600,
                      }}
                    >
                      {item.mode === "practice" ? "练习模式" : "模拟面试"}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.84rem", color: "var(--wj-text-secondary)", lineHeight: 1.6 }}>
                    当前可继续完成剩余轮次，保持问题上下文与回答反馈连续。
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "var(--wj-text-tertiary)" }}>最多 {item.max_turns} 轮</div>
                </button>
              ))}
            </div>
          ) : (
            <EmptyState
              title="还没有开始过模拟面试"
              description="选择一份简历和目标岗位，问鉴会根据你的真实经历设计面试计划。"
              action={
                <Link to="/app/interviews/new" className="btn-primary">
                  创建模拟面试
                </Link>
              }
            />
          )}
        </section>
      </div>

      <section className="app-surface" style={{ padding: "1.35rem 1.4rem" }}>
        <SectionHeading title="最近使用的简历" caption="从简历驱动下一轮问题设计" icon={FileText} />
        {data?.recent_resumes.length ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "0.9rem", marginTop: "1.1rem" }}>
            {data.recent_resumes.map((resume) => (
              <button
                key={resume.resume_id}
                type="button"
                onClick={() => navigate(`/app/resumes/${resume.resume_id}/profile`)}
                style={{
                  textAlign: "left",
                  border: "1px solid var(--wj-border-default)",
                  borderRadius: 16,
                  padding: "1rem",
                  background: "linear-gradient(180deg, #ffffff 0%, #fbfdff 100%)",
                  display: "grid",
                  gap: "0.45rem",
                }}
              >
                <div style={{ fontSize: "0.98rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>{resume.file_name}</div>
                <div style={{ fontSize: "0.84rem", color: "var(--wj-text-secondary)", lineHeight: 1.65 }}>
                  查看结构化画像、证据与主张，或直接基于该简历创建面试。
                </div>
                <div style={{ fontSize: "0.78rem", color: "var(--wj-text-tertiary)" }}>
                  上传于 {resume.created_at ? new Date(resume.created_at).toLocaleDateString("zh-CN") : "--"}
                </div>
              </button>
            ))}
          </div>
        ) : (
          <EmptyState
            title="从一份真实简历开始"
            description="上传简历后，问鉴会识别你的教育经历、项目经验和技能，并据此生成个性化面试问题。"
            action={
              <Link to="/app/resumes/new" className="btn-primary">
                上传第一份简历
              </Link>
            }
          />
        )}
      </section>
    </div>
  )
}

function ActionCard({
  icon: Icon,
  title,
  description,
  to,
  primary = false,
}: {
  icon: typeof MessageSquare
  title: string
  description: string
  to: string
  primary?: boolean
}) {
  return (
    <Link
      to={to}
      style={{
        display: "grid",
        gridTemplateColumns: "auto 1fr auto",
        gap: "0.8rem",
        alignItems: "center",
        padding: "1rem",
        borderRadius: 16,
        textDecoration: "none",
        background: primary ? "var(--wj-brand-primary)" : "var(--wj-bg-surface)",
        border: primary ? "1px solid var(--wj-brand-primary)" : "1px solid var(--wj-border-default)",
        color: primary ? "#ffffff" : "var(--wj-text-primary)",
        boxShadow: "var(--wj-shadow-sm)",
      }}
    >
      <div
        style={{
          width: 42,
          height: 42,
          borderRadius: 14,
          background: primary ? "rgba(255,255,255,0.12)" : "var(--wj-brand-accent-bg)",
          color: primary ? "#ffffff" : "var(--wj-brand-secondary)",
          display: "grid",
          placeItems: "center",
        }}
      >
        <Icon size={18} />
      </div>
      <div>
        <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>{title}</div>
        <div
          style={{
            marginTop: "0.28rem",
            fontSize: "0.8rem",
            lineHeight: 1.55,
            color: primary ? "rgba(255,255,255,0.78)" : "var(--wj-text-secondary)",
          }}
        >
          {description}
        </div>
      </div>
      <ArrowRight size={18} />
    </Link>
  )
}

function SectionHeading({
  title,
  caption,
  icon: Icon,
}: {
  title: string
  caption: string
  icon: typeof FileText
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem" }}>
      <div>
        <div className="app-eyebrow">Wenjian</div>
        <h2 style={{ margin: "0.35rem 0 0", fontSize: "1.1rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>{title}</h2>
        <p style={{ margin: "0.4rem 0 0", color: "var(--wj-text-secondary)", fontSize: "0.84rem" }}>{caption}</p>
      </div>
      <div
        style={{
          width: 42,
          height: 42,
          borderRadius: 14,
          background: "var(--wj-brand-accent-bg)",
          color: "var(--wj-brand-secondary)",
          display: "grid",
          placeItems: "center",
          flexShrink: 0,
        }}
      >
        <Icon size={18} />
      </div>
    </div>
  )
}

function MetricRow({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="app-muted-surface" style={{ padding: "0.95rem 1rem", display: "grid", gap: "0.2rem" }}>
      <span style={{ color: "var(--wj-text-tertiary)", fontSize: "0.76rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        {label}
      </span>
      <span style={{ color: "var(--wj-text-primary)", fontSize: "1.35rem", fontWeight: 700 }}>{value}</span>
      <span style={{ color: "var(--wj-text-secondary)", fontSize: "0.8rem" }}>{hint}</span>
    </div>
  )
}
