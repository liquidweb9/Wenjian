import { useAnalyticsSummary, useAnalyticsTrends } from "../hooks/use-analytics"
import { usePageTitle } from "@/lib/use-page-title"

export default function AnalyticsPage() {
  usePageTitle("/app/analytics")
  const { data: summary, isLoading: summaryLoading } = useAnalyticsSummary()
  const { data: trends, isLoading: trendsLoading } = useAnalyticsTrends()

  return (
    <div>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 600, marginBottom: "1.5rem" }}>能力分析</h2>

      {/* Summary cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <StatCard label="总面试数" value={summaryLoading ? null : (summary?.total_interviews ?? 0)} />
        <StatCard label="平均得分" value={summaryLoading ? null : (summary?.average_score ?? null)} suffix="分" />
        <StatCard label="验证率" value={summaryLoading ? null : (summary?.claim_verification_rate ?? null)} suffix="%" />
        <StatCard label="完成面试" value={summaryLoading ? null : _completedFromDistribution(summary?.score_distribution)} />
      </div>

      {/* Score distribution */}
      <div style={panelStyle}>
        <h3 style={sectionTitleStyle}>得分分布</h3>
        {summaryLoading ? (
          <p style={placeholderStyle}>加载中...</p>
        ) : !summary?.score_distribution ? (
          <p style={placeholderStyle}>暂无数据</p>
        ) : (
          <ScoreDistributionChart distribution={summary.score_distribution} />
        )}
      </div>

      {/* Abilities */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1rem" }}>
        <div style={panelStyle}>
          <h3 style={sectionTitleStyle}>优势能力</h3>
          {summaryLoading ? (
            <p style={placeholderStyle}>加载中...</p>
          ) : !summary?.top_abilities?.length ? (
            <p style={placeholderStyle}>暂无数据</p>
          ) : (
            <AbilityList items={summary.top_abilities} color="#22c55e" />
          )}
        </div>
        <div style={panelStyle}>
          <h3 style={sectionTitleStyle}>待提升能力</h3>
          {summaryLoading ? (
            <p style={placeholderStyle}>加载中...</p>
          ) : !summary?.weak_abilities?.length ? (
            <p style={placeholderStyle}>暂无数据</p>
          ) : (
            <AbilityList items={summary.weak_abilities} color="#e63946" />
          )}
        </div>
      </div>

      {/* Trends */}
      <div style={{ ...panelStyle, marginTop: "1rem" }}>
        <h3 style={sectionTitleStyle}>面试趋势</h3>
        {trendsLoading ? (
          <p style={placeholderStyle}>加载中...</p>
        ) : !trends?.interviews_over_time?.length ? (
          <p style={placeholderStyle}>暂无数据</p>
        ) : (
          <div>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
              {trends.interviews_over_time.slice(-12).map((item) => (
                <div
                  key={item.week}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: "0.25rem",
                  }}
                >
                  <div
                    style={{
                      width: 24,
                      height: Math.max(4, item.count * 12),
                      backgroundColor: "#0d1b2a",
                      borderRadius: "3px 3px 0 0",
                      minHeight: 4,
                    }}
                    title={`${item.week}: ${item.count} 场`}
                  />
                  <span style={{ fontSize: "0.6rem", color: "#94a3b8" }}>
                    {item.week.slice(-2)}
                  </span>
                </div>
              ))}
            </div>

            {/* Score trend */}
            {trends.score_trend.length > 0 && (
              <div style={{ marginTop: "1rem" }}>
                <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#64748b", marginBottom: "0.5rem" }}>
                  得分趋势
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                  {trends.score_trend.slice(-10).map((item) => (
                    <div key={item.date} style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                      <span style={{ fontSize: "0.75rem", color: "#94a3b8", width: 80 }}>{item.date}</span>
                      <div style={{ flex: 1, height: 8, backgroundColor: "#f1f5f9", borderRadius: "4px", overflow: "hidden" }}>
                        <div
                          style={{
                            height: "100%",
                            width: `${Math.min(100, (item.score / 100) * 100)}%`,
                            backgroundColor: item.score >= 70 ? "#22c55e" : item.score >= 50 ? "#f59e0b" : "#e63946",
                            borderRadius: "4px",
                          }}
                        />
                      </div>
                      <span style={{ fontSize: "0.8rem", fontWeight: 500, color: "#334155", width: 40, textAlign: "right" }}>
                        {item.score}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value, suffix, color }: {
  label: string
  value: number | null
  suffix?: string
  color?: string
}) {
  return (
    <div style={{
      backgroundColor: "#fff",
      padding: "1.5rem",
      borderRadius: "12px",
      border: "1px solid #e2e8f0",
    }}>
      <div style={{ fontSize: "0.85rem", color: "#64748b" }}>{label}</div>
      <div style={{
        fontSize: "2rem",
        fontWeight: 700,
        marginTop: "0.5rem",
        color: color ?? "#1e293b",
      }}>
        {value == null ? "--" : value}
        {value != null && suffix ? (
          <span style={{ fontSize: "1rem", fontWeight: 400, color: "#94a3b8" }}>{suffix}</span>
        ) : null}
      </div>
    </div>
  )
}

function ScoreDistributionChart({ distribution }: { distribution: Record<string, number> }) {
  const maxCount = Math.max(...Object.values(distribution), 1)
  const bucketOrder = ["0-20", "21-40", "41-60", "61-80", "81-100"]
  const colors = ["#e63946", "#f59e0b", "#f59e0b", "#0ea5a0", "#22c55e"]

  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: "1rem", height: 120, paddingTop: "0.5rem" }}>
      {bucketOrder.map((bucket, i) => {
        const count = distribution[bucket] ?? 0
        const height = count > 0 ? Math.max(8, (count / maxCount) * 100) : 0
        return (
          <div key={bucket} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
            <span style={{ fontSize: "0.7rem", color: "#64748b", marginBottom: "0.25rem" }}>{count}</span>
            <div
              style={{
                width: "100%",
                height,
                backgroundColor: colors[i],
                borderRadius: "4px 4px 0 0",
                opacity: 0.8,
              }}
            />
            <span style={{ fontSize: "0.65rem", color: "#94a3b8", marginTop: "0.25rem" }}>{bucket}</span>
          </div>
        )
      })}
    </div>
  )
}

function AbilityList({ items, color }: { items: Array<{ name: string; score: number }>; color: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      {items.map((item) => (
        <div key={item.name} style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ fontSize: "0.85rem", color: "#334155", flex: 1 }}>{item.name}</span>
          <div style={{ flex: 2, height: 8, backgroundColor: "#f1f5f9", borderRadius: "4px", overflow: "hidden" }}>
            <div
              style={{
                height: "100%",
                width: `${Math.min(100, (item.score / 100) * 100)}%`,
                backgroundColor: color,
                borderRadius: "4px",
              }}
            />
          </div>
          <span style={{ fontSize: "0.8rem", fontWeight: 500, color: "#334155", width: 36, textAlign: "right" }}>
            {item.score}
          </span>
        </div>
      ))}
    </div>
  )
}

function _completedFromDistribution(distribution?: Record<string, number>): number {
  if (!distribution) return 0
  return Object.values(distribution).reduce((a, b) => a + b, 0)
}

const panelStyle: React.CSSProperties = {
  backgroundColor: "#fff",
  borderRadius: "12px",
  border: "1px solid #e2e8f0",
  padding: "1.25rem",
}

const sectionTitleStyle: React.CSSProperties = {
  fontSize: "0.9rem",
  fontWeight: 600,
  color: "#334155",
  marginBottom: "1rem",
}

const placeholderStyle: React.CSSProperties = {
  color: "#94a3b8",
  fontSize: "0.85rem",
  textAlign: "center",
  padding: "1rem 0",
}
