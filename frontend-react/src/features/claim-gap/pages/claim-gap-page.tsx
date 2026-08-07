import React from "react"
import { useParams } from "react-router-dom"
import { PageHeader } from "@/components/common/page-header"
import { LoadingState } from "@/components/common/loading-state"
import { ErrorState } from "@/components/common/error-state"
import { EmptyState } from "@/components/common/empty-state"
import { usePageTitle } from "@/lib/use-page-title"
import { useGapAnalysis, useAnalyzeGap } from "@/features/claim-gap/hooks/use-claim-gap"
import { CoverageOverview } from "@/features/claim-gap/components/coverage-overview"
import { GapList } from "@/features/claim-gap/components/gap-list"
import { RequirementCoverage } from "@/features/claim-gap/components/requirement-coverage"

function ClaimGapPage() {
  usePageTitle("", "能力缺口分析")
  const { resumeId, jobTargetId } = useParams<{ resumeId: string; jobTargetId: string }>()

  const { data: analysis, isLoading, error } = useGapAnalysis(resumeId, jobTargetId)
  const analyzeGap = useAnalyzeGap()

  const handleReanalyze = async () => {
    if (!resumeId || !jobTargetId) return
    await analyzeGap.mutateAsync({ resume_id: resumeId, job_target_id: jobTargetId })
  }

  if (!resumeId || !jobTargetId) {
    return (
      <ErrorState
        title="缺少必要参数"
        message="需要提供简历 ID 和岗位目标 ID 才能进行能力缺口分析。"
      />
    )
  }

  if (isLoading) {
    return <LoadingState message="问鉴正在分析简历与岗位需求之间的能力缺口。" />
  }

  if (error) {
    return (
      <ErrorState
        title="能力缺口分析暂时无法完成"
        message={error instanceof Error ? error.message : "请稍后重新尝试。"}
        onRetry={handleReanalyze}
      />
    )
  }

  if (!analysis) {
    return (
      <EmptyState
        title="暂无分析结果"
        description="该简历与岗位目标的能力缺口尚未分析，点击下方按钮开始分析。"
        action={
          <button onClick={handleReanalyze} disabled={analyzeGap.isPending} className="btn-primary">
            {analyzeGap.isPending ? "分析中..." : "开始分析"}
          </button>
        }
      />
    )
  }

  return (
    <div>
      <PageHeader
        title="能力缺口分析"
        description="对比简历声明与岗位需求，识别覆盖情况与训练重点。"
        back={{ to: `/app/resumes/${resumeId}/claims`, label: "返回技术主张" }}
        action={
          <button onClick={handleReanalyze} disabled={analyzeGap.isPending} className="btn-primary">
            {analyzeGap.isPending ? "分析中..." : "重新分析"}
          </button>
        }
      />

      <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        <CoverageOverview analysis={analysis} />
        <RequirementCoverage analysis={analysis} />
        <GapList gaps={analysis.gaps} />
      </div>
    </div>
  )
}

export default ClaimGapPage
