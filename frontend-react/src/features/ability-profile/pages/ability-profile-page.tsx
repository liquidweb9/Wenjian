import { useParams } from "react-router-dom"
import { useAbilityProfile } from "../hooks/use-ability-profile"
import { usePageTitle } from "@/lib/use-page-title"
import { PageHeader } from "@/components/common/page-header"
import type {
  CompetencySummary,
  StabilityLevel,
  TransferStatus,
  ScoreTrend,
} from "@/lib/types/ability-profile"

export default function AbilityProfilePage() {
  usePageTitle("", "能力档案")
  const { resumeId } = useParams<{ resumeId: string }>()
  const { data, isLoading, isError, refetch } = useAbilityProfile(resumeId)

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <PageHeader
        title="能力档案"
        description="跨场次能力聚合：追踪同一简历在多次面试中的能力表现、稳定性与迁移验证。"
        back={{ to: `/app/resumes/${resumeId}/claims`, label: "返回技术主张" }}
      />

      {isLoading ? (
        <section className="app-surface" style={styles.centerBox}>
          正在汇总面试能力数据…
        </section>
      ) : isError ? (
        <section className="app-surface" style={styles.centerBox}>
          <div style={styles.emptyIcon}>⚠️</div>
          <div style={styles.emptyTitle}>加载能力档案失败</div>
          <p style={styles.emptyText}>
            无法读取该简历的能力数据，请确认你有权访问这份简历后重试。
          </p>
          <button onClick={() => refetch()} style={styles.retryButton}>
            重新加载
          </button>
        </section>
      ) : !data || data.competencies.length === 0 ? (
        <section className="app-surface" style={styles.centerBox}>
          <div style={styles.emptyIcon}>📊</div>
          <div style={styles.emptyTitle}>暂无能力档案</div>
          <p style={styles.emptyText}>
            尚未有完成面试的报告。完成至少一场面试后，这里会汇总各维度的能力评分、
            稳定性与跨场次趋势。
          </p>
        </section>
      ) : (
        <>
          <section className="app-surface" style={{ padding: "1.35rem 1.45rem" }}>
            <SummaryHeader totalInterviews={data.total_interviews} competencies={data.competencies} />
          </section>

          {data.competencies.map((summary) => (
            <CompetencyCard key={summary.competency_code} summary={summary} />
          ))}
        </>
      )}
    </div>
  )
}

function SummaryHeader({
  totalInterviews,
  competencies,
}: {
  totalInterviews: number
  competencies: CompetencySummary[]
}) {
  const avgScore =
    competencies.reduce((sum, c) => sum + c.profile.avg_score, 0) / competencies.length
  const highStabilityCount = competencies.filter(
    (c) => c.profile.stability === "HIGH",
  ).length
  const coveredCount = competencies.filter(
    (c) => c.profile.transfer_status !== "UNTESTED",
  ).length

  return (
    <div>
      <div className="app-eyebrow">Overview</div>
      <div style={styles.statsGrid}>
        <StatCard label="总面试数" value={String(totalInterviews)} />
        <StatCard label="能力维度" value={String(competencies.length)} />
        <StatCard label="平均能力分" value={avgScore.toFixed(1)} />
        <StatCard label="高稳定性能力" value={String(highStabilityCount)} />
        <StatCard label="已测迁移能力" value={String(coveredCount)} />
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div style={styles.statCard}>
      <div style={styles.statLabel}>{label}</div>
      <div style={styles.statValue}>{value}</div>
    </div>
  )
}

function CompetencyCard({ summary }: { summary: CompetencySummary }) {
  const { profile, history } = summary

  return (
    <section className="app-surface" style={{ padding: "1.35rem 1.45rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
        <div>
          <div style={styles.cardTitle}>{dimensionLabel(summary.competency_code)}</div>
          <div style={styles.cardCode}>{summary.competency_code}</div>
        </div>
        <StabilityBadge stability={profile.stability} />
      </div>

      <div style={styles.cardBody}>
        <div style={styles.metricsRow}>
          <Metric label="平均得分" value={`${profile.avg_score.toFixed(1)} / 100`} />
          <Metric
            label="得分趋势"
            value={<TrendValue trend={profile.score_trend} />}
          />
          <Metric label="迁移状态" value={<TransferValue status={profile.transfer_status} />} />
          <Metric label="问题形式" value={`${profile.forms_used.length} 种`} />
        </div>

        {history.length > 0 && <ScoreHistory history={history} />}

        <div style={styles.factorsGrid}>
          <FactorBar
            label="跨场次数"
            value={profile.stability_factors.session_count}
            max={3}
          />
          <FactorBar
            label="形式多样性"
            value={profile.stability_factors.form_diversity}
            max={4}
          />
          <FactorBar
            label="分数一致性"
            value={profile.stability_factors.score_consistency}
            max={1}
          />
          <FactorBar
            label="证据强度"
            value={profile.stability_factors.evidence_strength}
            max={1}
          />
        </div>

        {profile.forms_used.length > 0 && (
          <div style={styles.chipsRow}>
            {profile.forms_used.map((form) => (
              <span key={form} style={styles.chip}>
                {formatForm(form)}
              </span>
            ))}
          </div>
        )}

        {profile.unresolved_gaps.length > 0 && (
          <div style={styles.gapsBox}>
            <div style={styles.gapsLabel}>待补强</div>
            <div style={styles.chipsRow}>
              {profile.unresolved_gaps.map((gap) => (
                <span key={gap} style={styles.gapChip}>
                  {formatGap(gap)}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}

function Metric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div style={styles.metric}>
      <div style={styles.metricLabel}>{label}</div>
      <div style={styles.metricValue}>{value}</div>
    </div>
  )
}

function StabilityBadge({ stability }: { stability: StabilityLevel }) {
  const tones: Record<StabilityLevel, { bg: string; text: string; label: string }> = {
    HIGH: { bg: "#f0fdf4", text: "#166534", label: "高稳定性" },
    MEDIUM: { bg: "#fffbeb", text: "#b45309", label: "中等稳定性" },
    LOW: { bg: "#f1f5f9", text: "#64748b", label: "低稳定性" },
  }
  const tone = tones[stability]
  return (
    <span
      style={{
        padding: "0.28rem 0.7rem",
        borderRadius: 999,
        background: tone.bg,
        color: tone.text,
        fontSize: "0.78rem",
        fontWeight: 600,
      }}
    >
      {tone.label}
    </span>
  )
}

function TrendValue({ trend }: { trend: ScoreTrend }) {
  if (!trend) return <span style={{ color: "#94a3b8" }}>数据不足</span>
  const map: Record<Exclude<ScoreTrend, null>, { icon: string; color: string }> = {
    IMPROVING: { icon: "↗", color: "#16a34a" },
    STABLE: { icon: "→", color: "#2563eb" },
    DECLINING: { icon: "↘", color: "#dc2626" },
  }
  const item = map[trend]
  return (
    <span style={{ color: item.color, fontWeight: 600 }}>
      {item.icon} {formatTrend(trend)}
    </span>
  )
}

function TransferValue({ status }: { status: TransferStatus }) {
  const map: Record<TransferStatus, { label: string; color: string }> = {
    DEMONSTRATED: { label: "已验证迁移", color: "#16a34a" },
    PARTIAL: { label: "部分验证", color: "#ea580c" },
    UNTESTED: { label: "未测试", color: "#94a3b8" },
  }
  const item = map[status]
  return <span style={{ color: item.color }}>{item.label}</span>
}

function ScoreHistory({
  history,
}: {
  history: Array<{ interview_id: string; score: number; created_at: string | null }>
}) {
  const maxScore = Math.max(...history.map((h) => h.score), 1)
  return (
    <div style={styles.historyBox}>
      <div style={styles.historyLabel}>历次得分</div>
      <div style={styles.historyBars}>
        {history.map((h) => (
          <div key={h.interview_id} style={styles.historyBarCol}>
            <span style={styles.historyScore}>{h.score}</span>
            <div style={styles.historyBarTrack}>
              <div
                style={{
                  ...styles.historyBarFill,
                  height: `${Math.max(6, (h.score / maxScore) * 100)}%`,
                  backgroundColor: h.score >= 70 ? "#16a34a" : h.score >= 50 ? "#f59e0b" : "#dc2626",
                }}
              />
            </div>
            <span style={styles.historyDate}>{formatDate(h.created_at)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function FactorBar({
  label,
  value,
  max,
}: {
  label: string
  value: number
  max: number
}) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
        <span style={styles.factorLabel}>{label}</span>
        <span style={styles.factorValue}>{Math.round(value * 100) / 100}</span>
      </div>
      <div style={styles.factorTrack}>
        <div style={{ ...styles.factorFill, width: `${pct}%` }} />
      </div>
    </div>
  )
}

function formatTrend(trend: string): string {
  const map: Record<string, string> = {
    IMPROVING: "提升",
    STABLE: "稳定",
    DECLINING: "下降",
  }
  return map[trend] || trend
}

function formatForm(form: string): string {
  const map: Record<string, string> = {
    background: "背景职责",
    detail: "实现细节",
    deep: "深度追问",
    counterfactual: "反事实迁移",
    concept: "概念原理",
    project_detail: "项目细节",
    debugging: "排障分析",
    design_rationale: "设计理由",
    trade_off: "权衡取舍",
    production_scenario: "生产场景",
  }
  return map[form] || form
}

function formatGap(gap: string): string {
  const map: Record<string, string> = {
    LIMITED_FORM_DIVERSITY: "形式单一",
    NO_TRANSFER_TESTING: "缺迁移测试",
    INCOMPLETE_EVIDENCE: "证据不完整",
    INSUFFICIENT_DEPTH: "深度不足",
    UNRESOLVED_CONTRADICTIONS: "存在矛盾",
    SINGLE_SESSION_ONLY: "仅单场面试",
  }
  return map[gap] || gap
}

function formatDate(value: string | null): string {
  if (!value) return "--"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const dimensionLabels: Record<string, string> = {
  technical_correctness: "技术正确性",
  implementation_depth: "实现深度",
  architecture_tradeoffs: "架构权衡",
  personal_contribution: "个人贡献",
  production_awareness: "生产意识",
  clarity: "表达清晰度",
}

function dimensionLabel(name: string): string {
  return dimensionLabels[name] ?? name
}

const styles: Record<string, React.CSSProperties> = {
  centerBox: {
    padding: "2.5rem 1.5rem",
    textAlign: "center",
  },
  emptyIcon: { fontSize: "3rem", marginBottom: "0.75rem", color: "var(--wj-brand-secondary)" },
  emptyTitle: {
    fontSize: "1.1rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
    marginBottom: "0.5rem",
  },
  emptyText: {
    margin: "0.5rem auto 0",
    fontSize: "0.88rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.7,
    maxWidth: 480,
  },
  retryButton: {
    marginTop: "1rem",
    padding: "0.5rem 1.2rem",
    backgroundColor: "var(--wj-brand-primary)",
    color: "#fff",
    border: "none",
    borderRadius: "0.5rem",
    fontSize: "0.88rem",
    fontWeight: 600,
    cursor: "pointer",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
    gap: "1rem",
    marginTop: "1rem",
  },
  statCard: {
    padding: "1.1rem 1.2rem",
    backgroundColor: "var(--wj-bg-subtle)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.75rem",
    display: "grid",
    gap: "0.35rem",
  },
  statLabel: {
    fontSize: "0.78rem",
    fontWeight: 600,
    color: "var(--wj-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  statValue: { fontSize: "1.6rem", fontWeight: 700, color: "var(--wj-text-primary)" },
  cardTitle: {
    margin: 0,
    fontSize: "1.1rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
  },
  cardCode: {
    marginTop: "0.25rem",
    fontSize: "0.78rem",
    color: "var(--wj-text-tertiary)",
    fontFamily: '"JetBrains Mono", Consolas, monospace',
  },
  cardBody: { display: "grid", gap: "1.1rem", marginTop: "1rem" },
  metricsRow: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
    gap: "1rem",
  },
  metric: { display: "grid", gap: "0.25rem" },
  metricLabel: {
    fontSize: "0.75rem",
    fontWeight: 600,
    color: "var(--wj-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  metricValue: { fontSize: "0.95rem", fontWeight: 600, color: "var(--wj-text-primary)" },
  historyBox: { display: "grid", gap: "0.5rem" },
  historyLabel: {
    fontSize: "0.78rem",
    fontWeight: 600,
    color: "var(--wj-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  historyBars: { display: "flex", gap: "1.2rem", alignItems: "flex-end" },
  historyBarCol: { display: "grid", gap: "0.3rem", alignItems: "center", justifyItems: "center" },
  historyScore: { fontSize: "0.8rem", fontWeight: 600, color: "var(--wj-text-primary)" },
  historyBarTrack: {
    width: 26,
    height: 80,
    backgroundColor: "var(--wj-bg-subtle)",
    borderRadius: "0.4rem",
    display: "flex",
    alignItems: "flex-end",
    overflow: "hidden",
  },
  historyBarFill: { width: "100%", borderRadius: "0.4rem" },
  historyDate: { fontSize: "0.68rem", color: "var(--wj-text-tertiary)" },
  factorsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
    gap: "1rem",
  },
  factorLabel: { fontSize: "0.78rem", color: "var(--wj-text-secondary)" },
  factorValue: { fontSize: "0.78rem", fontWeight: 600, color: "var(--wj-text-primary)" },
  factorTrack: { height: 6, backgroundColor: "var(--wj-bg-subtle)", borderRadius: 999, overflow: "hidden" },
  factorFill: { height: "100%", backgroundColor: "var(--wj-brand-primary)", borderRadius: 999 },
  chipsRow: { display: "flex", flexWrap: "wrap", gap: "0.5rem" },
  chip: {
    padding: "0.25rem 0.6rem",
    backgroundColor: "var(--wj-bg-subtle)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.375rem",
    fontSize: "0.75rem",
    color: "var(--wj-text-secondary)",
  },
  gapsBox: {
    padding: "0.85rem 1rem",
    backgroundColor: "var(--wj-bg-subtle)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.5rem",
    display: "grid",
    gap: "0.5rem",
  },
  gapsLabel: {
    fontSize: "0.75rem",
    fontWeight: 600,
    color: "var(--wj-warning)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  gapChip: {
    padding: "0.25rem 0.6rem",
    backgroundColor: "var(--wj-warning-bg)",
    border: "1px solid rgba(245, 158, 11, 0.35)",
    borderRadius: "0.375rem",
    fontSize: "0.75rem",
    color: "var(--wj-warning)",
  },
}
