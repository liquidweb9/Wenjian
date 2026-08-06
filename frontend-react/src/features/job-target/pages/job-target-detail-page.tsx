import React from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { useJobTarget, useUpdateJobTarget, useDeleteJobTarget } from "@/features/job-target/hooks/use-job-targets"
import { RequirementEditor } from "@/features/job-target/components/requirement-editor"
import type { JobLevel, InterviewRound, RequirementCreateRequest } from "@/lib/types/job-target"

function JobTargetDetailPage() {
  const { jobTargetId } = useParams<{ jobTargetId: string }>()
  const navigate = useNavigate()

  const { data: jobTarget, isLoading, error } = useJobTarget(jobTargetId)
  const updateJobTarget = useUpdateJobTarget()
  const deleteJobTarget = useDeleteJobTarget()

  const [isEditing, setIsEditing] = React.useState(false)
  const [title, setTitle] = React.useState("")
  const [level, setLevel] = React.useState<JobLevel>("mid")
  const [round, setRound] = React.useState<InterviewRound>("technical")
  const [description, setDescription] = React.useState("")
  const [requirements, setRequirements] = React.useState<RequirementCreateRequest[]>([])

  React.useEffect(() => {
    if (jobTarget) {
      setTitle(jobTarget.title)
      setLevel(jobTarget.level)
      setRound(jobTarget.interview_round)
      setDescription(jobTarget.description || "")
      setRequirements(jobTarget.requirements.map(req => ({
        competency_code: req.competency_code,
        title: req.title,
        description: req.description || undefined,
        importance: req.importance,
        expected_level: req.expected_level,
        evidence_expectation: req.evidence_expectation,
      })))
    }
  }, [jobTarget])

  const handleSave = async () => {
    if (!jobTargetId) return

    try {
      await updateJobTarget.mutateAsync({
        jobTargetId,
        data: {
          title,
          level,
          interview_round: round,
          description: description || undefined,
          requirements,
        },
      })
      setIsEditing(false)
    } catch (err) {
      console.error("Failed to update job target:", err)
    }
  }

  const handleDelete = async () => {
    if (!jobTargetId) return
    if (!confirm("确定要删除此岗位吗？此操作不可撤销。")) return

    try {
      await deleteJobTarget.mutateAsync(jobTargetId)
      navigate("/app/job-targets")
    } catch (err) {
      console.error("Failed to delete job target:", err)
    }
  }

  if (isLoading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingText}>加载中...</div>
      </div>
    )
  }

  if (error || !jobTarget) {
    return (
      <div style={styles.container}>
        <div style={styles.errorBanner}>
          加载失败: {error instanceof Error ? error.message : "未知错误"}
        </div>
        <Link to="/app/job-targets" style={styles.backLink}>
          返回列表
        </Link>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.breadcrumb}>
        <Link to="/app/job-targets" style={styles.breadcrumbLink}>
          目标岗位
        </Link>
        <span style={styles.breadcrumbSeparator}>/</span>
        <span style={styles.breadcrumbCurrent}>{jobTarget.title}</span>
      </div>

      <div style={styles.header}>
        <h1 style={styles.title}>{jobTarget.title}</h1>
        <div style={styles.headerActions}>
          {isEditing ? (
            <>
              <button onClick={() => setIsEditing(false)} style={styles.cancelButton}>
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={updateJobTarget.isPending}
                style={{
                  ...styles.saveButton,
                  ...(updateJobTarget.isPending && styles.buttonDisabled),
                }}
              >
                {updateJobTarget.isPending ? "保存中..." : "保存"}
              </button>
            </>
          ) : (
            <>
              <button onClick={handleDelete} style={styles.deleteButton}>
                删除
              </button>
              <button onClick={() => setIsEditing(true)} style={styles.editButton}>
                编辑
              </button>
            </>
          )}
        </div>
      </div>

      <div style={styles.metaRow}>
        <div style={styles.badge}>{getLevelLabel(jobTarget.level)}</div>
        <div style={styles.badge}>{getRoundLabel(jobTarget.interview_round)}</div>
        <div style={styles.badge}>{getSourceLabel(jobTarget.source)}</div>
        <div style={styles.timestamp}>
          创建于 {new Date(jobTarget.created_at).toLocaleDateString("zh-CN")}
        </div>
      </div>

      {isEditing ? (
        <div style={styles.editSection}>
          <div style={styles.formGrid}>
            <div style={styles.formGroup}>
              <label style={styles.label}>岗位名称 *</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={styles.input}
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>岗位级别 *</label>
              <select value={level} onChange={(e) => setLevel(e.target.value as JobLevel)} style={styles.select}>
                <option value="intern">实习生</option>
                <option value="junior">初级</option>
                <option value="mid">中级</option>
                <option value="senior">高级</option>
                <option value="staff">资深</option>
              </select>
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>面试轮次</label>
              <select value={round} onChange={(e) => setRound(e.target.value as InterviewRound)} style={styles.select}>
                <option value="resume">简历筛选</option>
                <option value="project">项目面</option>
                <option value="technical">技术面</option>
                <option value="system_design">系统设计</option>
              </select>
            </div>

            <div style={{ ...styles.formGroup, gridColumn: "1 / -1" }}>
              <label style={styles.label}>岗位描述</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                style={styles.textarea}
              />
            </div>
          </div>

          <RequirementEditor requirements={requirements} onChange={setRequirements} />
        </div>
      ) : (
        <div style={styles.viewSection}>
          {jobTarget.description && (
            <div style={styles.descriptionSection}>
              <h2 style={styles.sectionTitle}>岗位描述</h2>
              <p style={styles.descriptionText}>{jobTarget.description}</p>
            </div>
          )}

          {jobTarget.raw_jd && (
            <div style={styles.jdSection}>
              <h2 style={styles.sectionTitle}>原始 JD</h2>
              <pre style={styles.jdText}>{jobTarget.raw_jd}</pre>
            </div>
          )}

          <div style={styles.requirementsSection}>
            <h2 style={styles.sectionTitle}>能力需求 ({jobTarget.requirements.length})</h2>
            <div style={styles.requirementsList}>
              {jobTarget.requirements.map((req, index) => (
                <div key={req.requirement_id} style={styles.requirementCard}>
                  <div style={styles.requirementHeader}>
                    <div style={styles.requirementIndex}>#{index + 1}</div>
                    <div style={styles.requirementTitle}>{req.title}</div>
                  </div>

                  {req.description && (
                    <div style={styles.requirementDescription}>{req.description}</div>
                  )}

                  <div style={styles.requirementMeta}>
                    <div style={styles.metaItem}>
                      <span style={styles.metaLabel}>重要度:</span>
                      <span style={styles.metaValue}>
                        {(req.importance * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div style={styles.metaItem}>
                      <span style={styles.metaLabel}>期望水平:</span>
                      <span style={styles.metaValue}>{req.expected_level}</span>
                    </div>
                    <div style={styles.metaItem}>
                      <span style={styles.metaLabel}>能力代码:</span>
                      <span style={styles.competencyCode}>{req.competency_code}</span>
                    </div>
                  </div>

                  <div style={styles.evidenceSection}>
                    <div style={styles.evidenceTitle}>证据期望:</div>
                    <ul style={styles.evidenceList}>
                      {req.evidence_expectation.map((evidence, evidenceIndex) => (
                        <li key={evidenceIndex} style={styles.evidenceItem}>
                          {evidence}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
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
    maxWidth: "1000px",
    margin: "0 auto",
  },
  breadcrumb: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "24px",
    fontSize: "14px",
  },
  breadcrumbLink: {
    color: "#2563eb",
    textDecoration: "none",
  },
  breadcrumbSeparator: {
    color: "#9ca3af",
  },
  breadcrumbCurrent: {
    color: "#6b7280",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "16px",
  },
  title: {
    fontSize: "28px",
    fontWeight: 600,
    color: "#1a1a1a",
    margin: 0,
  },
  headerActions: {
    display: "flex",
    gap: "12px",
  },
  editButton: {
    padding: "10px 20px",
    backgroundColor: "#2563eb",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    fontWeight: 500,
    fontSize: "14px",
    cursor: "pointer",
  },
  deleteButton: {
    padding: "10px 20px",
    backgroundColor: "#dc2626",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    fontWeight: 500,
    fontSize: "14px",
    cursor: "pointer",
  },
  cancelButton: {
    padding: "10px 20px",
    backgroundColor: "transparent",
    color: "#666",
    border: "1px solid #d1d5db",
    borderRadius: "8px",
    fontWeight: 500,
    fontSize: "14px",
    cursor: "pointer",
  },
  saveButton: {
    padding: "10px 20px",
    backgroundColor: "#2563eb",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    fontWeight: 500,
    fontSize: "14px",
    cursor: "pointer",
  },
  buttonDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
  },
  metaRow: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "32px",
  },
  badge: {
    padding: "6px 12px",
    backgroundColor: "#f3f4f6",
    color: "#4b5563",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: 500,
  },
  timestamp: {
    fontSize: "13px",
    color: "#9ca3af",
    marginLeft: "auto",
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
    marginBottom: "16px",
  },
  backLink: {
    color: "#2563eb",
    textDecoration: "none",
    fontSize: "14px",
  },
  editSection: {
    marginTop: "24px",
  },
  viewSection: {
    display: "flex",
    flexDirection: "column",
    gap: "32px",
  },
  descriptionSection: {},
  jdSection: {},
  requirementsSection: {},
  sectionTitle: {
    fontSize: "18px",
    fontWeight: 600,
    color: "#1a1a1a",
    marginBottom: "16px",
  },
  descriptionText: {
    fontSize: "14px",
    lineHeight: 1.6,
    color: "#4b5563",
    margin: 0,
  },
  jdText: {
    fontSize: "13px",
    lineHeight: 1.6,
    color: "#4b5563",
    backgroundColor: "#f9fafb",
    padding: "16px",
    borderRadius: "8px",
    border: "1px solid #e5e7eb",
    whiteSpace: "pre-wrap",
    fontFamily: "monospace",
    margin: 0,
  },
  requirementsList: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  requirementCard: {
    padding: "20px",
    backgroundColor: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: "10px",
  },
  requirementHeader: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "12px",
  },
  requirementIndex: {
    fontSize: "14px",
    fontWeight: 600,
    color: "#9ca3af",
  },
  requirementTitle: {
    fontSize: "16px",
    fontWeight: 600,
    color: "#1a1a1a",
  },
  requirementDescription: {
    fontSize: "14px",
    lineHeight: 1.6,
    color: "#6b7280",
    marginBottom: "16px",
  },
  requirementMeta: {
    display: "flex",
    gap: "24px",
    marginBottom: "16px",
    paddingBottom: "16px",
    borderBottom: "1px solid #f3f4f6",
  },
  metaItem: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "13px",
  },
  metaLabel: {
    color: "#9ca3af",
    fontWeight: 500,
  },
  metaValue: {
    color: "#1a1a1a",
    fontWeight: 600,
  },
  competencyCode: {
    padding: "4px 8px",
    backgroundColor: "#f3f4f6",
    color: "#4b5563",
    borderRadius: "4px",
    fontSize: "12px",
    fontFamily: "monospace",
  },
  evidenceSection: {},
  evidenceTitle: {
    fontSize: "13px",
    fontWeight: 600,
    color: "#6b7280",
    marginBottom: "8px",
  },
  evidenceList: {
    margin: 0,
    paddingLeft: "20px",
  },
  evidenceItem: {
    fontSize: "13px",
    lineHeight: 1.6,
    color: "#4b5563",
    marginBottom: "6px",
  },
  formGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: "20px",
    marginBottom: "32px",
  },
  formGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  label: {
    fontSize: "14px",
    fontWeight: 500,
    color: "#374151",
  },
  input: {
    padding: "10px 14px",
    fontSize: "14px",
    border: "1px solid #d1d5db",
    borderRadius: "6px",
  },
  select: {
    padding: "10px 14px",
    fontSize: "14px",
    border: "1px solid #d1d5db",
    borderRadius: "6px",
    backgroundColor: "#ffffff",
  },
  textarea: {
    padding: "10px 14px",
    fontSize: "14px",
    border: "1px solid #d1d5db",
    borderRadius: "6px",
    resize: "vertical",
    minHeight: "80px",
    fontFamily: "inherit",
  },
}

export default JobTargetDetailPage
