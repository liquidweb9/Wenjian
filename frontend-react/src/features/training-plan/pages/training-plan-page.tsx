import { useMemo, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { CheckCircle2, RotateCcw, Target, XCircle } from "lucide-react"
import {
  useGenerateTrainingPlan,
  useTrainingPlan,
  useUpdateTrainingTask,
} from "../hooks/use-training-plan"
import { usePageTitle } from "@/lib/use-page-title"
import { PageHeader } from "@/components/common/page-header"
import type { TrainingTask, TrainingTaskStatus } from "@/lib/types/training-plan"

type StatusFilter = "ALL" | TrainingTaskStatus

const taskTypeLabels: Record<string, string> = {
  EVIDENCE_COMPLETION: "补充证据",
  CONCEPT_REVIEW: "概念复习",
  DEPTH_IMPROVEMENT: "深度提升",
  CONTRADICTION_RESOLUTION: "矛盾澄清",
  FORM_DIVERSIFICATION: "形式多样化",
  TRANSFER_PRACTICE: "迁移练习",
}

const taskTypeTones: Record<string, { bg: string; text: string }> = {
  EVIDENCE_COMPLETION: { bg: "#f0fdf4", text: "#166534" },
  CONCEPT_REVIEW: { bg: "#eff6ff", text: "#1d4ed8" },
  DEPTH_IMPROVEMENT: { bg: "#fefce8", text: "#a16207" },
  CONTRADICTION_RESOLUTION: { bg: "#fef2f2", text: "#b91c1c" },
  FORM_DIVERSIFICATION: { bg: "#f5f3ff", text: "#6d28d9" },
  TRANSFER_PRACTICE: { bg: "#ecfeff", text: "#0e7490" },
}

const statusLabels: Record<TrainingTaskStatus, string> = {
  PENDING: "待开始",
  IN_PROGRESS: "进行中",
  COMPLETED: "已完成",
  DISMISSED: "已放弃",
}

const criteriaLabels: Record<string, string> = {
  target_evidence_status: "目标证据状态",
  required_details: "需要细节",
  min_verification_points: "最少验证点",
  target_form_count: "目标形式数",
  untested_forms: "待测形式",
  target_transfer_status: "目标迁移状态",
  min_counterfactual_scenarios: "最少反事实场景",
  min_counterfactual_score: "反事实最低分",
  target_avg_score: "目标平均分",
  target_max_depth: "目标深度",
  target_contradiction_count: "目标矛盾数",
  clarification_required: "需要澄清",
  target_concept_score: "目标概念分",
  recommended_resources: "推荐资源",
}

const statusFilterTabs: Array<{ value: StatusFilter; label: string }> = [
  { value: "ALL", label: "全部" },
  { value: "PENDING", label: "待开始" },
  { value: "IN_PROGRESS", label: "进行中" },
  { value: "COMPLETED", label: "已完成" },
  { value: "DISMISSED", label: "已放弃" },
]

export default function TrainingPlanPage() {
  usePageTitle("", "训练计划")
  const { resumeId } = useParams<{ resumeId: string }>()
  const navigate = useNavigate()

  const { data, isLoading, isError, refetch } = useTrainingPlan(resumeId)
  const generatePlan = useGenerateTrainingPlan(resumeId)
  const updateTask = useUpdateTrainingTask(resumeId)

  const [filter, setFilter] = useState<StatusFilter>("ALL")

  const tasks = useMemo(() => data?.tasks ?? [], [data])
  const visible = useMemo(
    () => (filter === "ALL" ? tasks : tasks.filter((task) => task.status === filter)),
    [filter, tasks],
  )
  const pendingCount = tasks.filter((t) => t.status === "PENDING").length
  const inProgressCount = tasks.filter((t) => t.status === "IN_PROGRESS").length
  const completedCount = tasks.filter((t) => t.status === "COMPLETED").length

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <PageHeader
        title="训练计划"
        description="根据面试中的证据缺口与能力短板生成可执行任务；完成后可启动复验，针对性验证是否真正补强。"
        back={{ to: `/app/resumes/${resumeId}/ability-profile`, label: "返回能力档案" }}
        action={
          <button
            type="button"
            className="btn-primary"
            disabled={generatePlan.isPending}
            onClick={() => generatePlan.mutate()}
          >
            {generatePlan.isPending ? "正在生成…" : "生成训练计划"}
          </button>
        }
      />

      {!isLoading && !isError ? (
        <section className="app-surface" style={{ padding: "1.5rem 1.6rem" }}>
          <div style={styles.statsGrid}>
            <StatCard label="待开始" value={pendingCount} tone="var(--wj-text-secondary)" />
            <StatCard label="进行中" value={inProgressCount} tone="#2563eb" />
            <StatCard label="已完成" value={completedCount} tone="var(--wj-success)" />
            <StatCard label="总任务" value={tasks.length} tone="var(--wj-brand-secondary)" />
          </div>
        </section>
      ) : null}

      {isLoading ? (
        <section className="app-surface" style={styles.centerBox}>
          正在加载训练计划…
        </section>
      ) : isError ? (
        <section className="app-surface" style={styles.centerBox}>
          <div style={styles.emptyTitle}>加载训练计划失败</div>
          <p style={styles.emptyText}>无法读取该简历的训练任务，请确认你有权访问后重试。</p>
          <button onClick={() => refetch()} style={styles.primaryButton}>
            重新加载
          </button>
        </section>
      ) : tasks.length === 0 ? (
        <section className="app-surface" style={styles.centerBox}>
          <Target size={40} color="var(--wj-brand-secondary)" />
          <div style={styles.emptyTitle}>暂无训练计划</div>
          <p style={styles.emptyText}>
            完成至少一场面试后，点击「生成训练计划」，问鉴会根据能力缺口和证据状态生成针对性任务。
          </p>
          <button
            onClick={() => generatePlan.mutate()}
            style={styles.primaryButton}
            disabled={generatePlan.isPending}
          >
            {generatePlan.isPending ? "正在生成…" : "立即生成"}
          </button>
        </section>
      ) : (
        <>
          <div style={styles.filterRow}>
            {statusFilterTabs.map((tab) => {
              const active = filter === tab.value
              return (
                <button
                  key={tab.value}
                  onClick={() => setFilter(tab.value)}
                  style={{
                    ...styles.filterTab,
                    ...(active ? styles.filterTabActive : {}),
                  }}
                >
                  {tab.label}
                </button>
              )
            })}
          </div>

          {visible.length === 0 ? (
            <section className="app-surface" style={styles.centerBox}>
              当前筛选下没有任务。
            </section>
          ) : (
            <div style={styles.taskList}>
              {visible.map((task) => (
                <TaskCard
                  key={task.task_id}
                  task={task}
                  onStatus={(status) => updateTask.mutate({ taskId: task.task_id, status })}
                  onReverify={() => navigate(`/app/interviews/new?resume_id=${resumeId}`)}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function StatCard({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div style={styles.statCard}>
      <div style={styles.statLabel}>{label}</div>
      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: tone }}>{value}</div>
    </div>
  )
}

function TaskCard({
  task,
  onStatus,
  onReverify,
}: {
  task: TrainingTask
  onStatus: (status: TrainingTaskStatus) => void
  onReverify: () => void
}) {
  const tone = taskTypeTones[task.task_type] ?? { bg: "#f1f5f9", text: "#475569" }
  const statusTone: Record<TrainingTaskStatus, { bg: string; text: string }> = {
    PENDING: { bg: "#f1f5f9", text: "#475569" },
    IN_PROGRESS: { bg: "#eff6ff", text: "#1d4ed8" },
    COMPLETED: { bg: "#f0fdf4", text: "#166534" },
    DISMISSED: { bg: "#f1f5f9", text: "#94a3b8" },
  }
  const st = statusTone[task.status]
  const isDone = task.status === "COMPLETED"
  const isDismissed = task.status === "DISMISSED"

  return (
    <section
      className="app-surface"
      style={{
        padding: "1.25rem 1.35rem",
        border: isDone ? "1px solid rgba(22,163,74,0.35)" : undefined,
        opacity: isDismissed ? 0.62 : 1,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "flex-start" }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap", marginBottom: "0.5rem" }}>
            <span style={{ ...styles.typeBadge, backgroundColor: tone.bg, color: tone.text }}>
              {taskTypeLabels[task.task_type] ?? task.task_type}
            </span>
            <span style={statusBadgeStyle(st)}>{statusLabels[task.status]}</span>
            <span style={styles.priorityBadge}>优先级 {task.priority}</span>
          </div>
          <div style={{ fontSize: "1.05rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>{task.title}</div>
          <div style={{ fontSize: "0.8rem", color: "var(--wj-text-tertiary)", marginTop: "0.25rem" }}>
            {task.competency_code}
          </div>
        </div>
        <div style={styles.actions}>
          {!isDone && !isDismissed ? (
            <>
              <button
                type="button"
                className="btn-primary"
                onClick={() => onStatus(task.status === "IN_PROGRESS" ? "COMPLETED" : "IN_PROGRESS")}
              >
                {task.status === "IN_PROGRESS" ? (
                  <>
                    <CheckCircle2 size={15} /> 标记完成
                  </>
                ) : (
                  "开始训练"
                )}
              </button>
              <button type="button" className="btn-secondary" onClick={() => onStatus("DISMISSED")}>
                <XCircle size={15} /> 放弃
              </button>
            </>
          ) : (
            <button type="button" className="btn-secondary" onClick={() => onStatus("PENDING")}>
              <RotateCcw size={15} /> 恢复
            </button>
          )}
        </div>
      </div>

      <p style={{ margin: "0.85rem 0 0", color: "var(--wj-text-secondary)", lineHeight: 1.75, fontSize: "0.88rem", whiteSpace: "pre-wrap" }}>
        {task.description}
      </p>

      <div style={styles.criteriaBox}>
        <div style={styles.criteriaLabel}>完成标准</div>
        <CriteriaList criteria={task.completion_criteria} />
      </div>

      <div style={{ marginTop: "1rem" }}>
        <button type="button" className="btn-primary" style={styles.reverifyButton} onClick={onReverify}>
          <RotateCcw size={15} />
          启动复验面试
        </button>
        <span style={styles.reverifyHint}>
          新建一场针对该简历的面试，用于验证任务是否真正补强。
        </span>
      </div>
    </section>
  )
}

function CriteriaList({
  criteria,
}: {
  criteria: Record<string, unknown> | unknown[]
}) {
  if (Array.isArray(criteria)) {
    if (criteria.length === 0) return <div style={styles.criteriaMuted}>无结构化标准</div>
    return (
      <ul style={styles.criteriaList}>
        {criteria.map((item, index) => (
          <li key={index}>{String(item)}</li>
        ))}
      </ul>
    )
  }

  const entries = Object.entries(criteria)
  if (entries.length === 0) return <div style={styles.criteriaMuted}>无结构化标准</div>
  return (
    <div style={styles.criteriaGrid}>
      {entries.map(([key, value]) => (
        <div key={key} style={styles.criteriaItem}>
          <span style={styles.criteriaKey}>{criteriaLabels[key] ?? key}</span>
          <span style={styles.criteriaValue}>{formatCriteriaValue(value)}</span>
        </div>
      ))}
    </div>
  )
}

function formatCriteriaValue(value: unknown): string {
  if (Array.isArray(value)) return value.join("、")
  if (typeof value === "boolean") return value ? "是" : "否"
  if (value == null) return "—"
  return String(value)
}

function statusBadgeStyle(st: { bg: string; text: string }): React.CSSProperties {
  return {
    padding: "0.22rem 0.6rem",
    borderRadius: "999px",
    backgroundColor: st.bg,
    color: st.text,
    fontSize: "0.76rem",
    fontWeight: 600,
  }
}

const styles: Record<string, React.CSSProperties> = {
  centerBox: { padding: "2.5rem 1.5rem", textAlign: "center", display: "grid", gap: "0.5rem", justifyItems: "center" },
  emptyTitle: { fontSize: "1.1rem", fontWeight: 600, color: "var(--wj-text-primary)" },
  emptyText: {
    margin: 0,
    fontSize: "0.88rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.7,
    maxWidth: 480,
  },
  primaryButton: {
    marginTop: "0.75rem",
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
    gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
    gap: "1rem",
  },
  statCard: {
    padding: "1rem 1.2rem",
    backgroundColor: "var(--wj-bg-subtle)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.75rem",
    display: "grid",
    gap: "0.3rem",
  },
  statLabel: {
    fontSize: "0.78rem",
    fontWeight: 600,
    color: "var(--wj-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  filterRow: { display: "flex", gap: "0.5rem", flexWrap: "wrap" },
  filterTab: {
    padding: "0.35rem 0.85rem",
    borderRadius: "999px",
    border: "1px solid var(--wj-border-default)",
    background: "var(--wj-bg-surface)",
    color: "var(--wj-text-secondary)",
    fontSize: "0.82rem",
    cursor: "pointer",
  },
  filterTabActive: {
    backgroundColor: "#0d1b2a",
    color: "#fff",
    border: "1px solid #0d1b2a",
  },
  taskList: { display: "grid", gap: "1rem" },
  typeBadge: {
    padding: "0.22rem 0.6rem",
    borderRadius: "0.375rem",
    fontSize: "0.76rem",
    fontWeight: 600,
  },
  priorityBadge: {
    padding: "0.22rem 0.6rem",
    borderRadius: "999px",
    backgroundColor: "#fefce8",
    color: "#a16207",
    fontSize: "0.76rem",
    fontWeight: 600,
  },
  actions: { display: "flex", gap: "0.5rem", flexShrink: 0 },
  criteriaBox: {
    marginTop: "0.9rem",
    padding: "0.85rem 1rem",
    backgroundColor: "var(--wj-bg-subtle)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.5rem",
  },
  criteriaLabel: {
    fontSize: "0.75rem",
    fontWeight: 600,
    color: "var(--wj-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    marginBottom: "0.5rem",
  },
  criteriaList: { margin: 0, paddingLeft: "1.1rem", color: "var(--wj-text-secondary)", fontSize: "0.84rem", lineHeight: 1.7 },
  criteriaGrid: { display: "grid", gap: "0.35rem" },
  criteriaItem: { display: "flex", justifyContent: "space-between", gap: "1rem", fontSize: "0.84rem" },
  criteriaKey: { color: "var(--wj-text-tertiary)" },
  criteriaValue: { color: "var(--wj-text-primary)", fontWeight: 500, textAlign: "right" },
  criteriaMuted: { color: "var(--wj-text-tertiary)", fontSize: "0.82rem" },
  reverifyButton: { display: "inline-flex", alignItems: "center", gap: "0.4rem" },
  reverifyHint: {
    marginLeft: "0.75rem",
    fontSize: "0.78rem",
    color: "var(--wj-text-tertiary)",
  },
}
