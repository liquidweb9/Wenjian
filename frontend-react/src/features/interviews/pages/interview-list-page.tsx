import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Plus } from "lucide-react"
import { PageHeader } from "@/components/common/page-header"
import { useInterviewList } from "../hooks/use-interviews"
import { usePageTitle } from "@/lib/use-page-title"

const statusLabels: Record<string, string> = {
  created: "已创建",
  in_progress: "进行中",
  finished: "已完成",
  failed: "失败",
}

const statusColors: Record<string, { bg: string; text: string }> = {
  created: { bg: "#f1f5f9", text: "#64748b" },
  in_progress: { bg: "#f0fbfa", text: "#0ea5a0" },
  finished: { bg: "#f0fdf4", text: "#16a34a" },
  failed: { bg: "#fef2f2", text: "#e63946" },
}

const modeLabels: Record<string, string> = {
  simulation: "模拟面试",
  practice: "练习模式",
}

export default function InterviewListPage() {
  usePageTitle("/app/interviews")
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState("")
  const [modeFilter, setModeFilter] = useState("")

  const { data, isLoading, isError } = useInterviewList({
    page,
    page_size: 10,
    status: statusFilter || undefined,
    mode: modeFilter || undefined,
  })

  return (
    <div>
      <PageHeader
        title="面试记录"
        description="查看全部模拟面试与练习记录：继续未完成的面试，或查看已完成面试的评分与教练反馈。"
        action={
          <Link to="/app/interviews/new" className="btn-primary">
            <Plus size={16} />
            新建面试
          </Link>
        }
      />

      {/* Filters */}
      <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem", flexWrap: "wrap" }}>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          style={selectStyle}
        >
          <option value="">全部状态</option>
          {Object.entries(statusLabels).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select
          value={modeFilter}
          onChange={(e) => { setModeFilter(e.target.value); setPage(1) }}
          style={selectStyle}
        >
          <option value="">全部模式</option>
          {Object.entries(modeLabels).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      {/* Loading */}
      {isLoading && (
        <div style={{ padding: "3rem", textAlign: "center", color: "#64748b" }}>
          加载中...
        </div>
      )}

      {/* Error */}
      {isError && (
        <div style={{
          backgroundColor: "#fff",
          borderRadius: "12px",
          border: "1px solid #e2e8f0",
          padding: "2rem",
          textAlign: "center",
          color: "#e63946",
        }}>
          加载失败，请重试
        </div>
      )}

      {/* Empty */}
      {data && data.items.length === 0 && (
        <div style={{ backgroundColor: "#fff", borderRadius: "12px", border: "1px solid #e2e8f0", padding: "3rem 2rem", textAlign: "center" }}>
          <p style={{ color: "#94a3b8", marginBottom: "0.5rem", fontSize: "0.95rem" }}>还没有开始过模拟面试</p>
          <p style={{ color: "#94a3b8", marginBottom: "1rem", fontSize: "0.85rem" }}>
            选择一份简历和目标岗位，问鉴会根据你的真实经历设计面试计划。
          </p>
          <Link to="/app/interviews/new" style={{ color: "#0ea5a0", textDecoration: "none", fontSize: "0.9rem" }}>
            创建第一场面试 →
          </Link>
        </div>
      )}

      {/* Table */}
      {data && data.items.length > 0 && (
        <>
          <div style={{
            backgroundColor: "#fff",
            borderRadius: "12px",
            border: "1px solid #e2e8f0",
            overflow: "hidden",
          }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #e2e8f0", backgroundColor: "#f8fafc" }}>
                  <th style={thStyle}>目标岗位</th>
                  <th style={thStyle}>模式</th>
                  <th style={thStyle}>状态</th>
                  <th style={thStyle}>轮次</th>
                  <th style={thStyle}>创建时间</th>
                  <th style={thStyle}>操作</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((it) => {
                  const sc = statusColors[it.status] ?? { bg: "#f1f5f9", text: "#64748b" }
                  return (
                    <tr key={it.interview_id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={tdStyle}>
                        <span style={{ fontWeight: 500 }}>{it.target_role || "—"}</span>
                      </td>
                      <td style={tdStyle}>{modeLabels[it.mode ?? ""] ?? it.mode ?? "—"}</td>
                      <td style={tdStyle}>
                        <span style={{
                          ...badgeStyle,
                          backgroundColor: sc.bg,
                          color: sc.text,
                        }}>
                          {statusLabels[it.status] ?? it.status}
                        </span>
                      </td>
                      <td style={tdStyle}>
                        {it.turn_count}/{it.max_turns}
                      </td>
                      <td style={{ ...tdStyle, color: "#94a3b8", fontSize: "0.8rem" }}>
                        {it.created_at ? new Date(it.created_at).toLocaleDateString("zh-CN") : "—"}
                      </td>
                      <td style={tdStyle}>
                        <div style={{ display: "flex", gap: "0.5rem" }}>
                          {!it.finished && (
                            <button
                              onClick={() => navigate(`/app/interviews/${it.interview_id}/live`)}
                              style={actionBtnStyle}
                            >
                              {it.turn_count > 0 ? "继续" : "开始"}
                            </button>
                          )}
                          {it.finished && (
                            <button
                              onClick={() => navigate(`/app/interviews/${it.interview_id}/report`)}
                              style={actionBtnStyle}
                            >
                              报告
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div style={{ display: "flex", justifyContent: "center", gap: "0.5rem", marginTop: "1rem" }}>
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                style={{ ...pageBtnStyle, opacity: page <= 1 ? 0.4 : 1 }}
              >
                上一页
              </button>
              <span style={{ padding: "0.4rem 0.8rem", fontSize: "0.85rem", color: "#64748b" }}>
                {page} / {data.pages}
              </span>
              <button
                disabled={page >= data.pages}
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                style={{ ...pageBtnStyle, opacity: page >= data.pages ? 0.4 : 1 }}
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

const selectStyle: React.CSSProperties = {
  padding: "0.4rem 0.75rem",
  borderRadius: "6px",
  border: "1px solid #e2e8f0",
  fontSize: "0.85rem",
  backgroundColor: "#fff",
  color: "#334155",
}

const thStyle: React.CSSProperties = {
  padding: "0.75rem 1rem",
  textAlign: "left",
  fontWeight: 600,
  fontSize: "0.8rem",
  color: "#64748b",
}

const tdStyle: React.CSSProperties = {
  padding: "0.75rem 1rem",
}

const badgeStyle: React.CSSProperties = {
  padding: "0.15rem 0.5rem",
  borderRadius: "4px",
  fontSize: "0.75rem",
  fontWeight: 500,
}

const actionBtnStyle: React.CSSProperties = {
  padding: "0.25rem 0.75rem",
  borderRadius: "4px",
  border: "1px solid #e2e8f0",
  backgroundColor: "transparent",
  color: "#0d1b2a",
  fontSize: "0.8rem",
  cursor: "pointer",
}

const pageBtnStyle: React.CSSProperties = {
  padding: "0.4rem 0.8rem",
  borderRadius: "6px",
  border: "1px solid #e2e8f0",
  backgroundColor: "#fff",
  color: "#334155",
  fontSize: "0.85rem",
  cursor: "pointer",
}
