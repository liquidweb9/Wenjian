import React, { useState } from "react"
import { useNavigate } from "react-router-dom"
import {
  useJobTargetTemplates,
  useCreateJobTarget,
  useParseJD,
} from "@/features/job-target/hooks/use-job-targets"
import { RequirementEditor } from "@/features/job-target/components/requirement-editor"
import type {
  JobLevel,
  InterviewRound,
  JobTargetTemplate,
  RequirementCreateRequest,
} from "@/lib/types/job-target"

type Step = "template" | "jd" | "requirements"
type CreationMode = "template" | "jd" | "manual"

function JobTargetCreatePage() {
  const navigate = useNavigate()
  const { data: templates } = useJobTargetTemplates()
  const createJobTarget = useCreateJobTarget()
  const parseJD = useParseJD()

  const [step, setStep] = useState<Step>("template")
  const [mode, setMode] = useState<CreationMode | null>(null)

  // Form state
  const [title, setTitle] = useState("")
  const [level, setLevel] = useState<JobLevel>("mid")
  const [round, setRound] = useState<InterviewRound>("technical")
  const [description, setDescription] = useState("")
  const [jdText, setJdText] = useState("")
  const [requirements, setRequirements] = useState<RequirementCreateRequest[]>([])

  const [isParsing, setIsParsing] = useState(false)
  const [parseError, setParseError] = useState<string | null>(null)

  const handleSelectTemplate = (template: JobTargetTemplate) => {
    setMode("template")
    setTitle(template.title)
    setLevel(template.level)
    setDescription(template.description)
    setRequirements(template.requirements)
    setStep("requirements")
  }

  const handleSelectJD = () => {
    setMode("jd")
    setStep("jd")
  }

  const handleSelectManual = () => {
    setMode("manual")
    setStep("requirements")
  }

  const handleParseJD = async () => {
    if (!jdText.trim()) return

    setIsParsing(true)
    setParseError(null)

    try {
      const result = await parseJD.mutateAsync({ jd_text: jdText })
      setRequirements(result.requirements)
      if (result.inferred_level) setLevel(result.inferred_level)
      if (result.inferred_round) setRound(result.inferred_round)
      setStep("requirements")
    } catch (err) {
      setParseError(err instanceof Error ? err.message : "解析失败")
    } finally {
      setIsParsing(false)
    }
  }

  const handleSubmit = async () => {
    if (!title.trim() || requirements.length === 0) {
      return
    }

    try {
      const newJobTarget = await createJobTarget.mutateAsync({
        title,
        level,
        interview_round: round,
        description: description || undefined,
        source: mode === "template" ? "template" : mode === "jd" ? "pasted_jd" : "manual",
        raw_jd: mode === "jd" ? jdText : undefined,
        requirements,
      })

      navigate(`/app/job-targets/${newJobTarget.job_target_id}`)
    } catch (err) {
      console.error("Failed to create job target:", err)
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>创建目标岗位</h1>
        <button onClick={() => navigate("/app/job-targets")} style={styles.cancelButton}>
          取消
        </button>
      </div>

      <div style={styles.stepIndicator}>
        <div style={{ ...styles.stepItem, ...(step === "template" ? styles.stepActive : {}) }}>
          1. 选择创建方式
        </div>
        {mode === "jd" && (
          <div style={{ ...styles.stepItem, ...(step === "jd" ? styles.stepActive : {}) }}>
            2. 粘贴 JD
          </div>
        )}
        <div style={{ ...styles.stepItem, ...(step === "requirements" ? styles.stepActive : {}) }}>
          {mode === "jd" ? "3" : "2"}. 编辑能力需求
        </div>
      </div>

      {step === "template" && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>选择创建方式</h2>

          <div style={styles.modeGrid}>
            <button onClick={handleSelectManual} style={styles.modeCard}>
              <div style={styles.modeIcon}>✏️</div>
              <div style={styles.modeTitle}>从空白创建</div>
              <div style={styles.modeDescription}>手动定义岗位信息和能力需求</div>
            </button>

            <button onClick={handleSelectJD} style={styles.modeCard}>
              <div style={styles.modeIcon}>📋</div>
              <div style={styles.modeTitle}>粘贴 JD</div>
              <div style={styles.modeDescription}>AI 自动解析岗位描述生成需求</div>
            </button>
          </div>

          <h3 style={styles.subsectionTitle}>或选择预设模板</h3>

          <div style={styles.templateGrid}>
            {templates?.map((template) => (
              <button
                key={template.id}
                onClick={() => handleSelectTemplate(template)}
                style={styles.templateCard}
              >
                <div style={styles.templateTitle}>{template.title}</div>
                <div style={styles.templateLevel}>{getLevelLabel(template.level)}</div>
                <div style={styles.templateDescription}>{template.description}</div>
                <div style={styles.templateStats}>
                  {template.requirements.length} 个能力需求
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {step === "jd" && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>粘贴岗位描述 (JD)</h2>

          <textarea
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="粘贴岗位描述内容，AI 将自动提取能力需求..."
            style={styles.jdTextarea}
          />

          {parseError && <div style={styles.errorBanner}>{parseError}</div>}

          <div style={styles.actionRow}>
            <button onClick={() => setStep("template")} style={styles.secondaryButton}>
              返回
            </button>
            <button
              onClick={handleParseJD}
              disabled={!jdText.trim() || isParsing}
              style={{
                ...styles.primaryButton,
                ...((!jdText.trim() || isParsing) && styles.buttonDisabled),
              }}
            >
              {isParsing ? "解析中..." : "解析 JD"}
            </button>
          </div>
        </div>
      )}

      {step === "requirements" && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>编辑岗位信息</h2>

          <div style={styles.formGrid}>
            <div style={styles.formGroup}>
              <label style={styles.label}>岗位名称 *</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="例如：Java 后端工程师"
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
                placeholder="简要描述岗位职责和要求..."
                style={styles.textarea}
              />
            </div>
          </div>

          <RequirementEditor
            requirements={requirements}
            onChange={setRequirements}
          />

          <div style={styles.actionRow}>
            <button onClick={() => navigate("/app/job-targets")} style={styles.secondaryButton}>
              取消
            </button>
            <button
              onClick={handleSubmit}
              disabled={!title.trim() || requirements.length === 0 || createJobTarget.isPending}
              style={{
                ...styles.primaryButton,
                ...((!title.trim() || requirements.length === 0 || createJobTarget.isPending) &&
                  styles.buttonDisabled),
              }}
            >
              {createJobTarget.isPending ? "创建中..." : "创建岗位"}
            </button>
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

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: "32px",
    maxWidth: "1000px",
    margin: "0 auto",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "24px",
  },
  title: {
    fontSize: "28px",
    fontWeight: 600,
    color: "#1a1a1a",
    margin: 0,
  },
  cancelButton: {
    padding: "8px 16px",
    backgroundColor: "transparent",
    color: "#666",
    border: "1px solid #d1d5db",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "14px",
  },
  stepIndicator: {
    display: "flex",
    gap: "16px",
    marginBottom: "32px",
    padding: "16px",
    backgroundColor: "#f9fafb",
    borderRadius: "8px",
  },
  stepItem: {
    flex: 1,
    padding: "12px",
    textAlign: "center",
    color: "#9ca3af",
    fontWeight: 500,
    fontSize: "14px",
    borderRadius: "6px",
  },
  stepActive: {
    backgroundColor: "#ffffff",
    color: "#2563eb",
    fontWeight: 600,
  },
  section: {
    marginBottom: "32px",
  },
  sectionTitle: {
    fontSize: "20px",
    fontWeight: 600,
    color: "#1a1a1a",
    marginBottom: "20px",
  },
  subsectionTitle: {
    fontSize: "16px",
    fontWeight: 600,
    color: "#4b5563",
    marginTop: "32px",
    marginBottom: "16px",
  },
  modeGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: "16px",
    marginBottom: "32px",
  },
  modeCard: {
    padding: "24px",
    backgroundColor: "#ffffff",
    border: "2px solid #e5e7eb",
    borderRadius: "12px",
    cursor: "pointer",
    textAlign: "center",
    transition: "border-color 0.2s, box-shadow 0.2s",
  },
  modeIcon: {
    fontSize: "48px",
    marginBottom: "12px",
  },
  modeTitle: {
    fontSize: "18px",
    fontWeight: 600,
    color: "#1a1a1a",
    marginBottom: "8px",
  },
  modeDescription: {
    fontSize: "14px",
    color: "#666",
    lineHeight: 1.5,
  },
  templateGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
    gap: "16px",
  },
  templateCard: {
    padding: "20px",
    backgroundColor: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: "10px",
    cursor: "pointer",
    textAlign: "left",
    transition: "border-color 0.2s, box-shadow 0.2s",
  },
  templateTitle: {
    fontSize: "16px",
    fontWeight: 600,
    color: "#1a1a1a",
    marginBottom: "6px",
  },
  templateLevel: {
    display: "inline-block",
    padding: "4px 10px",
    backgroundColor: "#dbeafe",
    color: "#1e40af",
    borderRadius: "6px",
    fontSize: "11px",
    fontWeight: 500,
    marginBottom: "10px",
  },
  templateDescription: {
    fontSize: "13px",
    color: "#666",
    lineHeight: 1.5,
    marginBottom: "12px",
  },
  templateStats: {
    fontSize: "12px",
    color: "#9ca3af",
    fontWeight: 500,
  },
  jdTextarea: {
    width: "100%",
    minHeight: "300px",
    padding: "16px",
    fontSize: "14px",
    lineHeight: 1.6,
    border: "1px solid #d1d5db",
    borderRadius: "8px",
    resize: "vertical",
    fontFamily: "inherit",
  },
  errorBanner: {
    padding: "12px 16px",
    backgroundColor: "#fef2f2",
    color: "#991b1b",
    borderRadius: "6px",
    fontSize: "14px",
    marginTop: "16px",
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
  actionRow: {
    display: "flex",
    justifyContent: "flex-end",
    gap: "12px",
    marginTop: "32px",
  },
  primaryButton: {
    padding: "10px 24px",
    backgroundColor: "#2563eb",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    fontWeight: 500,
    fontSize: "14px",
    cursor: "pointer",
  },
  secondaryButton: {
    padding: "10px 24px",
    backgroundColor: "transparent",
    color: "#666",
    border: "1px solid #d1d5db",
    borderRadius: "8px",
    fontWeight: 500,
    fontSize: "14px",
    cursor: "pointer",
  },
  buttonDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
  },
}

export default JobTargetCreatePage
