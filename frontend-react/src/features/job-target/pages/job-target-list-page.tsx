import React from "react"
import { Link } from "react-router-dom"
import { useJobTargets } from "@/features/job-target/hooks/use-job-targets"
import type { JobLevel, InterviewRound } from "@/lib/types/job-target"

function JobTargetListPage() {
  const { data: jobTargets, isLoading, error } = useJobTargets()

  if (isLoading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingText}>加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.errorBanner}>
          加载失败: {error instanceof Error ? error.message : "未知错误"}
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>目标岗位管理</h1>
        <Link to="/app/job-targets/create" style={styles.createButton}>
          + 创建新岗位
        </Link>
      </div>

      {jobTargets && jobTargets.length === 0 ? (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>📋</div>
          <div style={styles.emptyTitle}>暂无目标岗位</div>
          <div style={styles.emptyDescription}>
            创建目标岗位以开始设计针对性的面试评估
          </div>
          <Link to="/app/job-targets/create" style={styles.emptyButton}>
            创建第一个岗位
          </Link>
        </div>
      ) : (
        <div style={styles.grid}>
          {jobTargets?.map((jobTarget) => (
            <Link
              key={jobTarget.job_target_id}
              to={`/app/job-targets/${jobTarget.job_target_id}`}
              style={styles.card}
            >
              <div style={styles.cardHeader}>
                <div style={styles.cardTitle}>{jobTarget.title}</div>
                <div style={styles.badges}>
                  <span style={styles.levelBadge}>{getLevelLabel(jobTarget.level)}</span>
                  <span style={styles.roundBadge}>{getRoundLabel(jobTarget.interview_round)}</span>
                </div>
              </div>

              {jobTarget.description && (
                <div style={styles.cardDescription}>{jobTarget.description}</div>
              )}

              <div style={styles.cardStats}>
                <div style={styles.statItem}>
                  <span style={styles.statValue}>{jobTarget.requirements.length}</span>
                  <span style={styles.statLabel}>能力需求</span>
                </div>
                <div style={styles.statItem}>
                  <span style={styles.statValue}>
                    {jobTarget.requirements.filter((r) => r.importance >= 0.8).length}
                  </span>
                  <span style={styles.statLabel}>核心能力</span>
                </div>
              </div>

              <div style={styles.cardFooter}>
                <span style={styles.sourceBadge}>{getSourceLabel(jobTarget.source)}</span>
                <span style={styles.timestamp}>
                  {new Date(jobTarget.created_at).toLocaleDateString("zh-CN")}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
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

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: "32px",
    maxWidth: "1200px",
    margin: "0 auto",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "32px",
  },
  title: {
    fontSize: "28px",
    fontWeight: 600,
    color: "#1a1a1a",
    margin: 0,
  },
  createButton: {
    padding: "10px 20px",
    backgroundColor: "#2563eb",
    color: "#ffffff",
    borderRadius: "8px",
    textDecoration: "none",
    fontWeight: 500,
    fontSize: "14px",
    transition: "background-color 0.2s",
  },
  loadingText: {
    textAlign: "center",
    color: "#666",
    fontSize: "16px",
    padding: "60px 0",
  },
  errorBanner: {
    padding: "16px",
    backgroundColor: "#fef2f2",
    color: "#991b1b",
    borderRadius: "8px",
    border: "1px solid #fecaca",
  },
  emptyState: {
    textAlign: "center",
    padding: "80px 20px",
  },
  emptyIcon: {
    fontSize: "64px",
    marginBottom: "16px",
  },
  emptyTitle: {
    fontSize: "20px",
    fontWeight: 600,
    color: "#1a1a1a",
    marginBottom: "8px",
  },
  emptyDescription: {
    fontSize: "14px",
    color: "#666",
    marginBottom: "24px",
  },
  emptyButton: {
    display: "inline-block",
    padding: "10px 24px",
    backgroundColor: "#2563eb",
    color: "#ffffff",
    borderRadius: "8px",
    textDecoration: "none",
    fontWeight: 500,
    fontSize: "14px",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))",
    gap: "24px",
  },
  card: {
    display: "block",
    padding: "24px",
    backgroundColor: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: "12px",
    textDecoration: "none",
    color: "inherit",
    transition: "box-shadow 0.2s, border-color 0.2s",
    cursor: "pointer",
  },
  cardHeader: {
    marginBottom: "12px",
  },
  cardTitle: {
    fontSize: "18px",
    fontWeight: 600,
    color: "#1a1a1a",
    marginBottom: "8px",
  },
  badges: {
    display: "flex",
    gap: "8px",
  },
  levelBadge: {
    padding: "4px 12px",
    backgroundColor: "#dbeafe",
    color: "#1e40af",
    borderRadius: "6px",
    fontSize: "12px",
    fontWeight: 500,
  },
  roundBadge: {
    padding: "4px 12px",
    backgroundColor: "#f3e8ff",
    color: "#6b21a8",
    borderRadius: "6px",
    fontSize: "12px",
    fontWeight: 500,
  },
  cardDescription: {
    fontSize: "14px",
    color: "#666",
    lineHeight: 1.5,
    marginBottom: "16px",
    display: "-webkit-box",
    WebkitLineClamp: 2,
    WebkitBoxOrient: "vertical",
    overflow: "hidden",
  },
  cardStats: {
    display: "flex",
    gap: "24px",
    padding: "16px 0",
    borderTop: "1px solid #f3f4f6",
    borderBottom: "1px solid #f3f4f6",
    marginBottom: "16px",
  },
  statItem: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  statValue: {
    fontSize: "20px",
    fontWeight: 600,
    color: "#1a1a1a",
  },
  statLabel: {
    fontSize: "12px",
    color: "#666",
  },
  cardFooter: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  sourceBadge: {
    padding: "4px 10px",
    backgroundColor: "#f3f4f6",
    color: "#4b5563",
    borderRadius: "6px",
    fontSize: "11px",
    fontWeight: 500,
  },
  timestamp: {
    fontSize: "12px",
    color: "#9ca3af",
  },
}

export default JobTargetListPage
