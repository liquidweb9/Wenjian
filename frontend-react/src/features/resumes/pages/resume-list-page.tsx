import { useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { Plus } from "lucide-react"
import { useResumeList, useDeleteResume } from "../hooks/use-resumes"
import { ApiError } from "@/lib/api-client"
import { getResumeErrorMessage } from "../utils/error-mapping"
import { PageHeader } from "@/components/common/page-header"
import { EmptyState } from "@/components/common/empty-state"
import { ErrorState } from "@/components/common/error-state"
import { LoadingState } from "@/components/common/loading-state"
import { usePageTitle } from "@/lib/use-page-title"

const statusLabels: Record<string, string> = {
  UPLOADED: "已上传",
  PARSED_UNCONFIRMED: "待确认",
  CONFIRMED: "已确认",
  SUPERSEDED: "已替换",
  FAILED: "解析失败",
}

const statusStyles: Record<string, { bg: string; text: string }> = {
  UPLOADED: { bg: "#f1f5f9", text: "#475569" },
  PARSED_UNCONFIRMED: { bg: "#fffbeb", text: "#b45309" },
  CONFIRMED: { bg: "#f0fdf4", text: "#166534" },
  SUPERSEDED: { bg: "#f8fafc", text: "#64748b" },
  FAILED: { bg: "#fef2f2", text: "#b91c1c" },
}

export default function ResumeListPage() {
  usePageTitle("/app/resumes")
  const [searchParams, setSearchParams] = useSearchParams()
  const page = Number(searchParams.get("page") || 1)
  const search = searchParams.get("search") || ""
  const statusFilter = searchParams.get("status") || ""
  const [inputValue, setInputValue] = useState(search)

  const { data, isLoading, isError, error } = useResumeList({
    page,
    page_size: 20,
    search: search || undefined,
    status: statusFilter || undefined,
  })

  const deleteMutation = useDeleteResume()
  const [deleting, setDeleting] = useState<string | null>(null)

  function updateParams(updates: Record<string, string>) {
    const next = new URLSearchParams(searchParams)
    for (const [key, value] of Object.entries(updates)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    if (updates.search !== undefined || updates.status !== undefined) next.set("page", "1")
    setSearchParams(next, { replace: true })
  }

  async function handleDelete(resumeId: string) {
    if (!confirm("确定删除这份简历吗？相关面试与报告也可能受影响。")) return
    setDeleting(resumeId)
    try {
      await deleteMutation.mutateAsync(resumeId)
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div>
      <PageHeader
        title="简历管理"
        description="上传并确认真实简历，整理教育、项目、工作经历与主张证据，为后续模拟面试提供可靠输入。"
        brand
        action={
          <Link to="/app/resumes/new" className="btn-primary">
            <Plus size={16} />
            上传简历
          </Link>
        }
      />

      <section className="app-surface" style={{ padding: "1rem", marginBottom: "1.25rem" }}>
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 180px auto", gap: "0.75rem" }}>
          <input
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") updateParams({ search: inputValue })
            }}
            placeholder="按文件名搜索简历"
            style={inputStyle}
          />
          <select
            value={statusFilter}
            onChange={(event) => updateParams({ status: event.target.value })}
            style={inputStyle}
          >
            <option value="">全部状态</option>
            {Object.entries(statusLabels).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
          <button type="button" className="btn-secondary" onClick={() => updateParams({ search: inputValue })}>
            搜索
          </button>
        </div>
      </section>

      {isLoading ? <LoadingState message="问鉴正在整理简历列表与状态。" /> : null}
      {isError ? (
        <ErrorState
          title="简历列表暂时无法加载"
          message={error instanceof ApiError ? getResumeErrorMessage(error.code) : "请稍后重新尝试。"}
        />
      ) : null}

      {!isLoading && !isError && data?.total === 0 ? (
        <EmptyState
          title="从一份真实简历开始"
          description="上传简历后，问鉴会识别你的教育经历、项目经验和技能，并据此生成个性化面试问题。"
          action={
            <Link to="/app/resumes/new" className="btn-primary">
              上传第一份简历
            </Link>
          }
        />
      ) : null}

      {!isLoading && !isError && data && data.total > 0 ? (
        <div style={{ display: "grid", gap: "0.9rem" }}>
          {data.items.map((resume) => {
            const statusStyle = statusStyles[resume.status ?? ""] ?? { bg: "#f1f5f9", text: "#475569" }
            return (
              <section
                key={resume.resume_id}
                className="app-surface"
                style={{
                  padding: "1.15rem 1.2rem",
                  display: "grid",
                  gridTemplateColumns: "minmax(0, 1.4fr) 0.6fr 0.8fr auto",
                  gap: "1rem",
                  alignItems: "center",
                }}
              >
                <div>
                  <div className="app-eyebrow">Resume Record</div>
                  <div style={{ marginTop: "0.35rem", fontSize: "1rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
                    {resume.file_name}
                  </div>
                  <div style={{ marginTop: "0.4rem", color: "var(--wj-text-secondary)", fontSize: "0.84rem" }}>
                    类型：{resume.source_type?.toUpperCase() || "UNKNOWN"} · 上传于{" "}
                    {resume.created_at ? new Date(resume.created_at).toLocaleDateString("zh-CN") : "--"}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: "0.76rem", color: "var(--wj-text-tertiary)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                    解析状态
                  </div>
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      marginTop: "0.35rem",
                      padding: "0.25rem 0.65rem",
                      borderRadius: 999,
                      background: statusStyle.bg,
                      color: statusStyle.text,
                      fontSize: "0.8rem",
                      fontWeight: 600,
                    }}
                  >
                    {statusLabels[resume.status ?? ""] ?? resume.status ?? "未知"}
                  </span>
                </div>

                <div>
                  <div style={{ fontSize: "0.76rem", color: "var(--wj-text-tertiary)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                    推荐动作
                  </div>
                  <div style={{ marginTop: "0.35rem", color: "var(--wj-text-secondary)", fontSize: "0.84rem", lineHeight: 1.6 }}>
                    {resume.status === "CONFIRMED"
                      ? "可直接创建模拟面试，进入连续追问流程。"
                      : "建议先完成确认或重试解析，再进入面试。"}
                  </div>
                </div>

                <div style={{ display: "flex", gap: "0.55rem", justifyContent: "flex-end", flexWrap: "wrap" }}>
                  <Link to={`/app/resumes/${resume.resume_id}/review`} className="btn-secondary">
                    查看
                  </Link>
                  {resume.status === "CONFIRMED" ? (
                    <Link to={`/app/interviews/new?resume_id=${resume.resume_id}`} className="btn-primary">
                      创建面试
                    </Link>
                  ) : null}
                  <button
                    type="button"
                    className="btn-danger"
                    disabled={deleting === resume.resume_id}
                    onClick={() => handleDelete(resume.resume_id)}
                  >
                    {deleting === resume.resume_id ? "删除中…" : "删除"}
                  </button>
                </div>
              </section>
            )
          })}

          {data.pages > 1 ? (
            <div style={{ display: "flex", justifyContent: "center", gap: "0.75rem", marginTop: "0.6rem" }}>
              <button
                type="button"
                className="btn-secondary"
                disabled={page <= 1}
                onClick={() => updateParams({ page: String(page - 1) })}
              >
                上一页
              </button>
              <div className="app-muted-surface" style={{ padding: "0.65rem 0.95rem", color: "var(--wj-text-secondary)" }}>
                第 {page} / {data.pages} 页
              </div>
              <button
                type="button"
                className="btn-secondary"
                disabled={page >= data.pages}
                onClick={() => updateParams({ page: String(page + 1) })}
              >
                下一页
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  minHeight: 46,
  padding: "0.75rem 0.9rem",
  borderRadius: 12,
  border: "1px solid var(--wj-border-default)",
  background: "var(--wj-bg-surface)",
  color: "var(--wj-text-primary)",
}
