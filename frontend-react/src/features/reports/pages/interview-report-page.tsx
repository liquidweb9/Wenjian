import { useParams } from "react-router-dom"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { BrandMark } from "@/components/brand/BrandLogo"
import { EmptyState } from "@/components/common/empty-state"
import { LoadingState } from "@/components/common/loading-state"
import { useReport } from "../hooks/use-report"
import { useInterview } from "@/features/interviews/hooks/use-interviews"
import { usePageTitle } from "@/lib/use-page-title"
import { BRAND } from "@/lib/brand"

export default function InterviewReportPage() {
  const { interviewId } = useParams<{ interviewId: string }>()
  usePageTitle("", "面试报告")

  const { data: reportData, isLoading } = useReport(interviewId)
  const { data: interview } = useInterview(interviewId)
  const report = reportData?.report

  if (isLoading) {
    return <LoadingState message="问鉴正在准备本次面试分析报告。" />
  }

  if (!report) {
    return (
      <EmptyState
        title="完成一次面试后生成专业报告"
        description={
          interview?.status === "finished"
            ? "报告正在整理中，请稍后刷新查看。"
            : "报告将汇总回答评分、能力表现、证据一致性和后续训练建议。"
        }
      />
    )
  }

  const summaryObj =
    report.summary && typeof report.summary === "object" && !Array.isArray(report.summary)
      ? (report.summary as Record<string, unknown>)
      : null
  const summaryText = typeof report.summary === "string" ? report.summary : ""
  const reportText = (report.report_text as string) || (report.text as string) || ""
  const abilityEntries = Object.entries((report.abilities ?? report.ability_scores ?? {}) as Record<string, number>)
  const claimEntries = Object.entries((report.claim_statuses ?? report.claims ?? {}) as Record<string, unknown>)
  const questions = (report.questions ?? report.question_details ?? []) as Array<Record<string, unknown>>
  const suggestions = (report.resume_suggestions ?? report.suggestions ?? []) as string[]
  const learningPlan = (report.learning_plan ?? report.study_plan ?? []) as Array<Record<string, unknown>>

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <section className="app-surface" style={{ padding: "1.5rem 1.6rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "flex-start" }}>
          <div style={{ display: "flex", gap: "0.95rem", alignItems: "flex-start" }}>
            <BrandMark size={42} />
            <div>
              <div className="app-eyebrow">Wenjian Interview Assessment Report</div>
              <h1 style={{ margin: "0.45rem 0 0", fontSize: "1.7rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
                问鉴面试分析报告
              </h1>
              <p style={{ margin: "0.55rem 0 0", color: "var(--wj-text-secondary)", lineHeight: 1.7 }}>
                {interview?.target_role || "未指定目标岗位"} · {BRAND.chineseName} {BRAND.englishName}
              </p>
            </div>
          </div>

          <div className="app-muted-surface" style={{ padding: "0.9rem 1rem", minWidth: 280 }}>
            <MetaRow label="候选人或用户" value="当前工作区用户" />
            <MetaRow label="目标岗位" value={interview?.target_role || "未指定"} />
            <MetaRow label="面试时间" value={reportData?.created_at || "--"} />
            <MetaRow label="报告生成时间" value={String(reportData?.created_at || "--")} />
          </div>
        </div>
      </section>

      <section className="app-surface" style={{ padding: "1.35rem 1.45rem" }}>
        <SectionTitle index={1} title="总体结论" />
        <div style={{ display: "grid", gridTemplateColumns: "260px minmax(0, 1fr)", gap: "1rem", marginTop: "1rem" }}>
          <OverallScoreCard report={report} summaryObj={summaryObj} />
          <div>
            <p style={{ margin: 0, color: "var(--wj-text-secondary)", lineHeight: 1.75 }}>
              {summaryText || "本报告依据问鉴在本场模拟面试中的问题、回答、评分与证据一致性分析自动生成。"}
            </p>
            {reportText ? (
              <div style={{ marginTop: "1rem" }}>
                <MarkdownBlock content={extractNumberedSections(reportText, [1]) || reportText} />
              </div>
            ) : null}
          </div>
        </div>
      </section>

      <section className="app-surface" style={{ padding: "1.35rem 1.45rem" }}>
        <SectionTitle index={2} title="核心能力评分" />
        {abilityEntries.length ? (
          <div style={{ display: "grid", gap: "0.85rem", marginTop: "1rem" }}>
            {abilityEntries.sort((a, b) => b[1] - a[1]).map(([name, score]) => (
              <div key={name}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", marginBottom: "0.35rem" }}>
                  <span style={{ color: "var(--wj-text-primary)", fontWeight: 500 }}>{dimensionLabel(name)}</span>
                  <strong style={{ color: "var(--wj-text-primary)" }}>{score} / 100</strong>
                </div>
                <div style={{ height: 10, background: "var(--wj-bg-subtle)", borderRadius: 999, overflow: "hidden" }}>
                  <div
                    style={{
                      height: "100%",
                      width: `${Math.min(score, 100)}%`,
                      background: score >= 70 ? "var(--wj-success)" : score >= 50 ? "var(--wj-warning)" : "var(--wj-error)",
                      borderRadius: 999,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <MarkdownBlock content={extractNumberedSections(reportText, [2]) || "暂无结构化能力评分。"} />
        )}
      </section>

      <section className="app-surface" style={{ padding: "1.35rem 1.45rem" }}>
        <SectionTitle index={3} title="关键优势" />
        <MarkdownBlock content={extractNumberedSections(reportText, [3]) || "报告暂未单独整理出关键优势。"} />
      </section>

      <section className="app-surface" style={{ padding: "1.35rem 1.45rem" }}>
        <SectionTitle index={4} title="主要问题" />
        <MarkdownBlock content={extractNumberedSections(reportText, [4]) || "报告暂未单独整理出主要问题。"} />
      </section>

      <section className="app-surface" style={{ padding: "1.35rem 1.45rem" }}>
        <SectionTitle index={5} title="典型回答" />
        {questions.length ? (
          <div style={{ display: "grid", gap: "0.85rem", marginTop: "1rem" }}>
            {questions.map((question, index) => (
              <div key={index} className="app-muted-surface" style={{ padding: "1rem" }}>
                <div style={{ color: "var(--wj-brand-secondary)", fontSize: "0.78rem", fontWeight: 700 }}>Q{index + 1}</div>
                <div style={{ marginTop: "0.45rem", color: "var(--wj-text-primary)", fontWeight: 600, lineHeight: 1.65 }}>
                  {(question.question_text as string) || `问题 ${index + 1}`}
                </div>
                <div style={{ marginTop: "0.55rem", color: "var(--wj-text-secondary)", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
                  {(question.answer_text as string) || "暂无记录回答。"}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <MarkdownBlock content={extractNumberedSections(reportText, [5]) || "暂无结构化问答详情。"} />
        )}
      </section>

      <section className="app-surface" style={{ padding: "1.35rem 1.45rem" }}>
        <SectionTitle index={6} title="简历证据一致性" />
        {claimEntries.length ? (
          <div style={{ display: "grid", gap: "0.75rem", marginTop: "1rem" }}>
            {claimEntries.map(([claimId, claimStatus]) => (
              <div key={claimId} className="app-muted-surface" style={{ padding: "0.95rem 1rem", display: "flex", justifyContent: "space-between", gap: "1rem" }}>
                <div style={{ color: "var(--wj-text-primary)", fontFamily: "\"JetBrains Mono\", Consolas, monospace" }}>{claimId}</div>
                <ClaimStatusPill value={claimStatus} />
              </div>
            ))}
          </div>
        ) : (
          <MarkdownBlock content={extractNumberedSections(reportText, [6]) || "暂无结构化证据一致性数据。"} />
        )}
      </section>

      <section className="app-surface" style={{ padding: "1.35rem 1.45rem" }}>
        <SectionTitle index={7} title="改进建议" />
        {suggestions.length ? (
          <ul style={{ margin: "1rem 0 0", paddingLeft: "1.2rem", color: "var(--wj-text-secondary)", lineHeight: 1.75 }}>
            {suggestions.map((suggestion, index) => (
              <li key={index} style={{ marginBottom: "0.35rem" }}>
                {suggestion}
              </li>
            ))}
          </ul>
        ) : (
          <MarkdownBlock content={extractNumberedSections(reportText, [7]) || "暂无结构化改进建议。"} />
        )}
      </section>

      <section className="app-surface" style={{ padding: "1.35rem 1.45rem" }}>
        <SectionTitle index={8} title="后续训练计划" />
        {learningPlan.length ? (
          <div style={{ display: "grid", gap: "0.8rem", marginTop: "1rem" }}>
            {learningPlan.map((item, index) => (
              <div key={index} className="app-muted-surface" style={{ padding: "1rem" }}>
                <div style={{ color: "var(--wj-text-primary)", fontWeight: 600 }}>
                  {(item.topic ?? item.title ?? `训练项 ${index + 1}`) as string}
                </div>
                {(item.description ?? item.detail) ? (
                  <p style={{ margin: "0.45rem 0 0", color: "var(--wj-text-secondary)", lineHeight: 1.7 }}>
                    {(item.description ?? item.detail) as string}
                  </p>
                ) : null}
              </div>
            ))}
          </div>
        ) : (
          <MarkdownBlock content={extractNumberedSections(reportText, [8]) || "暂无结构化训练计划。"} />
        )}
      </section>

      <footer className="app-surface" style={{ padding: "1rem 1.2rem", textAlign: "center", color: "var(--wj-text-secondary)", fontSize: "0.84rem" }}>
        由问鉴 Wenjian 生成 · 简历驱动的 AI 模拟面试平台
      </footer>
    </div>
  )
}

function OverallScoreCard({
  report,
  summaryObj,
}: {
  report: Record<string, unknown>
  summaryObj: Record<string, unknown> | null
}) {
  const overallScore =
    (summaryObj?.overall_score as number | undefined) ??
    (report.overall_score as number | undefined) ??
    (report.score as number | undefined)

  const totalQuestions = summaryObj?.total_questions as number | undefined
  const answeredQuestions = summaryObj?.questions_answered as number | undefined
  const claimsVerified = summaryObj?.claims_verified as number | undefined

  return (
    <div className="app-muted-surface" style={{ padding: "1rem" }}>
      <div className="app-eyebrow">Overall Score</div>
      <div style={{ marginTop: "0.55rem", fontSize: "2.4rem", fontWeight: 700, color: "var(--wj-text-primary)" }}>
        {overallScore ?? "--"}
      </div>
      <div style={{ color: "var(--wj-text-secondary)", fontSize: "0.84rem" }}>总分 / 100</div>
      <div style={{ display: "grid", gap: "0.5rem", marginTop: "1rem" }}>
        <MetaRow label="总问题数" value={totalQuestions != null ? String(totalQuestions) : "--"} />
        <MetaRow label="已回答问题" value={answeredQuestions != null ? String(answeredQuestions) : "--"} />
        <MetaRow label="已验证主张" value={claimsVerified != null ? String(claimsVerified) : "--"} />
      </div>
    </div>
  )
}

function ClaimStatusPill({ value }: { value: unknown }) {
  const status = typeof value === "string" ? value : ((value as Record<string, unknown>)?.status as string) || "UNKNOWN"
  const tones: Record<string, { bg: string; text: string }> = {
    VERIFIED: { bg: "#f0fdf4", text: "#166534" },
    PARTIALLY_VERIFIED: { bg: "#fffbeb", text: "#b45309" },
    CONTRADICTED: { bg: "#fef2f2", text: "#b91c1c" },
    UNVERIFIED: { bg: "#fef2f2", text: "#dc2626" },
    UNTOUCHED: { bg: "#f1f5f9", text: "#475569" },
    UNKNOWN: { bg: "#f1f5f9", text: "#475569" },
  }
  const tone = tones[status] ?? { bg: "#f1f5f9", text: "#475569" }

  return (
    <span
      style={{
        alignSelf: "start",
        padding: "0.22rem 0.6rem",
        borderRadius: 999,
        background: tone.bg,
        color: tone.text,
        fontSize: "0.78rem",
        fontWeight: 600,
      }}
    >
      {status}
    </span>
  )
}

function SectionTitle({ index, title }: { index: number; title: string }) {
  return (
    <div>
      <div className="app-eyebrow">Section {index}</div>
      <h2 style={{ margin: "0.45rem 0 0", fontSize: "1.2rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
        {title}
      </h2>
    </div>
  )
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", marginBottom: "0.35rem", fontSize: "0.82rem" }}>
      <span style={{ color: "var(--wj-text-tertiary)" }}>{label}</span>
      <span style={{ color: "var(--wj-text-primary)", fontWeight: 500, textAlign: "right" }}>{value}</span>
    </div>
  )
}

function MarkdownBlock({ content }: { content: string }) {
  return (
    <div className="markdown-body">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  )
}

function extractNumberedSections(content: string, wanted: number[]) {
  if (!content) return ""
  const lines = content.split("\n")
  const selected: string[] = []
  let include = false

  for (const line of lines) {
    const match = line.match(/^#{1,6}\s*(\d+)[.、：:\s]/)
    if (match) include = wanted.includes(Number(match[1]))
    if (include) selected.push(line)
  }

  return selected.join("\n").trim()
}

const dimensionLabels: Record<string, string> = {
  technical_correctness: "技术正确性",
  implementation_depth: "实现深度",
  architecture_tradeoffs: "架构权衡",
  personal_contribution: "个人贡献",
  production_awareness: "生产意识",
  clarity: "表达清晰度",
}

function dimensionLabel(name: string) {
  return dimensionLabels[name] ?? name
}
