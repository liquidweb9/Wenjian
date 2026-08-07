import React from "react"
import { Link } from "react-router-dom"
import { Plus } from "lucide-react"
import { PageHeader } from "@/components/common/page-header"
import { LoadingState } from "@/components/common/loading-state"
import { ErrorState } from "@/components/common/error-state"
import { EmptyState } from "@/components/common/empty-state"
import { usePageTitle } from "@/lib/use-page-title"
import { useJobTargets } from "@/features/job-target/hooks/use-job-targets"
import type { JobLevel, InterviewRound } from "@/lib/types/job-target"

function JobTargetListPage() {
  usePageTitle("/app/job-targets")
  const { data: jobTargets, isLoading, error } = useJobTargets()

  return (
    <div>
      <PageHeader
        title="目标岗位管理"
        description="管理你正在准备的岗位目标：从模板、JD 解析或空白创建，并为每个岗位配置能力需求以指导面试评估。"
        action={
          <Link to="/app/job-targets/create" className="btn-primary">
            <Plus size={16} />
            创建新岗位
          </Link>
        }
      />

      {isLoading ? <LoadingState message="问鉴正在整理目标岗位列表。" /> : null}
      {error ? (
        <ErrorState
          title="目标岗位列表暂时无法加载"
          message={error instanceof Error ? error.message : "请稍后重新尝试。"}
        />
      ) : null}

      {!isLoading && !error && jobTargets && jobTargets.length === 0 ? (
        <EmptyState
          title="还没有目标岗位"
          description="创建目标岗位以开始设计针对性的面试评估。"
          action={
            <Link to="/app/job-targets/create" className="btn-primary">
              创建第一个岗位
            </Link>
          }
        />
      ) : null}

      {!isLoading && !error && jobTargets && jobTargets.length > 0 ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "1rem" }}>
          {jobTargets.map((jobTarget) => (
            <Link
              key={jobTarget.job_target_id}
              to={`/app/job-targets/${jobTarget.job_target_id}`}
              className="app-surface"
              style={{
                display: "block",
                padding: "1.25rem 1.3rem",
                textDecoration: "none",
                color: "inherit",
                transition: "box-shadow 0.2s, border-color 0.2s",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
                <div style={{ fontSize: "1.02rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
                  {jobTarget.title}
                </div>
                <div style={{ display: "flex", gap: "0.4rem", flexShrink: 0 }}>
                  <span style={badgeStyle("#dbeafe", "#1e40af")}>{getLevelLabel(jobTarget.level)}</span>
                  <span style={badgeStyle("#f3e8ff", "#6b21a8")}>{getRoundLabel(jobTarget.interview_round)}</span>
                </div>
              </div>

              {jobTarget.description ? (
                <div
                  style={{
                    marginTop: "0.6rem",
                    fontSize: "0.88rem",
                    color: "var(--wj-text-secondary)",
                    lineHeight: 1.6,
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }}
                >
                  {jobTarget.description}
                </div>
              ) : null}

              <div
                style={{
                  display: "flex",
                  gap: "1.5rem",
                  padding: "0.9rem 0",
                  marginTop: "0.9rem",
                  borderTop: "1px solid var(--wj-border-subtle)",
                  borderBottom: "1px solid var(--wj-border-subtle)",
                }}
              >
                <div>
                  <div style={statValueStyle}>{jobTarget.requirements.length}</div>
                  <div style={statLabelStyle}>能力需求</div>
                </div>
                <div>
                  <div style={statValueStyle}>
                    {jobTarget.requirements.filter((r) => r.importance >= 0.8).length}
                  </div>
                  <div style={statLabelStyle}>核心能力</div>
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.9rem" }}>
                <span style={badgeStyle("#f3f4f6", "#4b5563")}>{getSourceLabel(jobTarget.source)}</span>
                <span style={{ fontSize: "0.78rem", color: "var(--wj-text-tertiary)" }}>
                  {new Date(jobTarget.created_at).toLocaleDateString("zh-CN")}
                </span>
              </div>
            </Link>
          ))}
        </div>
      ) : null}
    </div>
  )
}

function getLevelLabel(level: JobLevel): string {
  const labels: Record<JobLevel, string> = {
    intern: "实习生",
    junior: "初级",
    mid: "中级",
    senior: "高级",
    staff: "资深",
  }
  return labels[level]
}

function getRoundLabel(round: InterviewRound): string {
  const labels: Record<InterviewRound, string> = {
    resume: "简历筛选",
    project: "项目面",
    technical: "技术面",
    system_design: "系统设计",
  }
  return labels[round]
}

function getSourceLabel(source: string): string {
  const labels: Record<string, string> = {
    template: "模板",
    pasted_jd: "JD解析",
    manual: "手动创建",
  }
  return labels[source] || source
}

function badgeStyle(bg: string, text: string): React.CSSProperties {
  return {
    padding: "0.2rem 0.6rem",
    backgroundColor: bg,
    color: text,
    borderRadius: "6px",
    fontSize: "0.72rem",
    fontWeight: 500,
    whiteSpace: "nowrap",
  }
}

const statValueStyle: React.CSSProperties = {
  fontSize: "1.15rem",
  fontWeight: 600,
  color: "var(--wj-text-primary)",
}

const statLabelStyle: React.CSSProperties = {
  fontSize: "0.72rem",
  color: "var(--wj-text-secondary)",
  marginTop: "0.15rem",
}

export default JobTargetListPage
