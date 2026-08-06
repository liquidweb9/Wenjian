import React from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { useGapAnalysis, useAnalyzeGap } from "@/features/claim-gap/hooks/use-claim-gap"
import { CoverageOverview } from "@/features/claim-gap/components/coverage-overview"
import { GapList } from "@/features/claim-gap/components/gap-list"
import { RequirementCoverage } from "@/features/claim-gap/components/requirement-coverage"
import { useResume } from "@/features/resumes/hooks/use-resumes"
import { useJobTarget } from "@/features/job-target/hooks/use-job-targets"

function ClaimGapPage() {
  const { resumeId, jobTargetId } = useParams<{ resumeId: string; jobTargetId: string }>()
  const navigate = useNavigate()

  const { data: analysis, isLoading, error } = useGapAnalysis(resumeId, jobTargetId)
  const analyzeGap = useAnalyzeGap()

  const { data: resume } = useResume(resumeId)
  const { data: jobTarget } = useJobTarget(jobTargetId)

  const handleReanalyze = async () => {
    if (!resumeId || !jobTargetId) return
    await analyzeGap.mutateAsync({ resume_id: resumeId, job_target_id: jobTargetId })
  }

  if (!resumeId || !jobTargetId) {
    return (
      <div style={styles.container}>
        <div style={styles.errorCard}>
          <h2 style={styles.errorTitle}>缺少必要参数</h2>
          <p style={styles.errorText}>需要提供简历 ID 和岗位目标 ID</p>
          <button onClick={() => navigate("/app/resumes")} style={styles.backButton}>
            返回简历列表
          </button>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingCard}>
          <div style={styles.spinner} />
          <p style={styles.loadingText}>加载能力缺口分析...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.errorCard}>
          <h2 style={styles.errorTitle}>加载失败</h2>
          <p style={styles.errorText}>
            {error instanceof Error ? error.message : "未知错误"}
          </p>
          <div style={styles.errorActions}>
            <button onClick={handleReanalyze} style={styles.retryButton}>
              重新分析
            </button>
            <button onClick={() => navigate("/app/resumes")} style={styles.backButton}>
              返回简历列表
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!analysis) {
    return (
      <div style={styles.container}>
        <div style={styles.emptyCard}>
          <h2 style={styles.emptyTitle}>暂无分析结果</h2>
          <p style={styles.emptyText}>
            该简历与岗位目标的能力缺口尚未分析，点击下方按钮开始分析
          </p>
          <button
            onClick={handleReanalyze}
            disabled={analyzeGap.isPending}
            style={styles.analyzeButton}
          >
            {analyzeGap.isPending ? "分析中..." : "开始分析"}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* Breadcrumb */}
      <div style={styles.breadcrumb}>
        <Link to="/app/resumes" style={styles.breadcrumbLink}>
          简历管理
        </Link>
        <span style={styles.breadcrumbSeparator}>/</span>
        {resume && (
          <>
            <Link to={`/app/resumes/${resumeId}`} style={styles.breadcrumbLink}>
              {resume.file_name}
            </Link>
            <span style={styles.breadcrumbSeparator}>/</span>
          </>
        )}
        <Link to="/app/job-targets" style={styles.breadcrumbLink}>
          目标岗位
        </Link>
        <span style={styles.breadcrumbSeparator}>/</span>
        {jobTarget && (
          <>
            <Link to={`/app/job-targets/${jobTargetId}`} style={styles.breadcrumbLink}>
              {jobTarget.title}
            </Link>
            <span style={styles.breadcrumbSeparator}>/</span>
          </>
        )}
        <span style={styles.breadcrumbCurrent}>能力缺口分析</span>
      </div>

      {/* Page Header */}
      <div style={styles.pageHeader}>
        <div>
          <h1 style={styles.pageTitle}>能力缺口分析</h1>
          <p style={styles.pageSubtitle}>
            对比简历声明与岗位需求，识别覆盖情况与训练重点
          </p>
        </div>
        <button
          onClick={handleReanalyze}
          disabled={analyzeGap.isPending}
          style={styles.reanalyzeButton}
        >
          {analyzeGap.isPending ? "分析中..." : "重新分析"}
        </button>
      </div>

      {/* Main Content */}
      <div style={styles.content}>
        {/* Coverage Overview */}
        <div style={styles.section}>
          <CoverageOverview analysis={analysis} />
        </div>

        {/* Requirement Coverage */}
        <div style={styles.section}>
          <RequirementCoverage analysis={analysis} />
        </div>

        {/* Gap List */}
        <div style={styles.section}>
          <GapList gaps={analysis.gaps} />
        </div>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: "1200px",
    margin: "0 auto",
    padding: "24px",
  },
  breadcrumb: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "24px",
    fontSize: "13px",
  },
  breadcrumbLink: {
    color: "#6b7280",
    textDecoration: "none",
    transition: "color 0.2s",
  },
  breadcrumbSeparator: {
    color: "#d1d5db",
  },
  breadcrumbCurrent: {
    color: "#1a1a1a",
    fontWeight: 500,
  },
  pageHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "32px",
  },
  pageTitle: {
    fontSize: "28px",
    fontWeight: 700,
    color: "#1a1a1a",
    margin: "0 0 8px 0",
  },
  pageSubtitle: {
    fontSize: "14px",
    color: "#6b7280",
    margin: 0,
  },
  reanalyzeButton: {
    padding: "10px 20px",
    fontSize: "14px",
    fontWeight: 600,
    color: "#ffffff",
    backgroundColor: "#7c3aed",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    transition: "background-color 0.2s",
  },
  content: {
    display: "flex",
    flexDirection: "column",
    gap: "24px",
  },
  section: {
    width: "100%",
  },
  loadingCard: {
    padding: "64px 32px",
    backgroundColor: "#ffffff",
    borderRadius: "12px",
    border: "1px solid #e5e7eb",
    textAlign: "center",
  },
  spinner: {
    width: "40px",
    height: "40px",
    margin: "0 auto 16px",
    border: "4px solid #e5e7eb",
    borderTop: "4px solid #7c3aed",
    borderRadius: "50%",
    animation: "spin 1s linear infinite",
  },
  loadingText: {
    fontSize: "14px",
    color: "#6b7280",
    margin: 0,
  },
  errorCard: {
    padding: "48px 32px",
    backgroundColor: "#ffffff",
    borderRadius: "12px",
    border: "1px solid #fecaca",
    textAlign: "center",
  },
  errorTitle: {
    fontSize: "20px",
    fontWeight: 600,
    color: "#dc2626",
    margin: "0 0 12px 0",
  },
  errorText: {
    fontSize: "14px",
    color: "#6b7280",
    margin: "0 0 24px 0",
  },
  errorActions: {
    display: "flex",
    gap: "12px",
    justifyContent: "center",
  },
  retryButton: {
    padding: "10px 24px",
    fontSize: "14px",
    fontWeight: 600,
    color: "#ffffff",
    backgroundColor: "#7c3aed",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
  },
  backButton: {
    padding: "10px 24px",
    fontSize: "14px",
    fontWeight: 600,
    color: "#6b7280",
    backgroundColor: "#f9fafb",
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
    cursor: "pointer",
  },
  emptyCard: {
    padding: "64px 32px",
    backgroundColor: "#ffffff",
    borderRadius: "12px",
    border: "1px solid #e5e7eb",
    textAlign: "center",
  },
  emptyTitle: {
    fontSize: "20px",
    fontWeight: 600,
    color: "#1a1a1a",
    margin: "0 0 12px 0",
  },
  emptyText: {
    fontSize: "14px",
    color: "#6b7280",
    margin: "0 0 24px 0",
    lineHeight: 1.6,
  },
  analyzeButton: {
    padding: "12px 32px",
    fontSize: "14px",
    fontWeight: 600,
    color: "#ffffff",
    backgroundColor: "#7c3aed",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
  },
}

export default ClaimGapPage
