import { usePreferenceStore, type ModelTier } from "@/stores/preference-store"
import { PageHeader } from "@/components/common/page-header"
import { usePageTitle } from "@/lib/use-page-title"

const modelTierLabels: Record<ModelTier, string> = {
  auto: "自动（按任务路由）",
  fast: "快速（fast）",
  balanced: "均衡（balanced）",
  judge: "深度判定（judge）",
}

export default function SettingsPage() {
  usePageTitle("/app/settings")
  const preferences = usePreferenceStore()

  return (
    <div style={{ maxWidth: 720, margin: "0 auto" }}>
      <PageHeader
        title="设置"
        description="配置默认面试偏好，设置会保存在本地，并在下次创建面试时自动生效。"
        back={{ to: "/app/dashboard", label: "返回工作台" }}
      />

      {/* Interview preferences */}
      <div style={sectionStyle}>
        <h3 style={sectionTitleStyle}>面试偏好</h3>

        <div style={fieldStyle}>
          <label style={labelStyle}>默认模式</label>
          <select
            value={preferences.defaultMode}
            onChange={(e) => preferences.setDefaultMode(e.target.value)}
            style={selectStyle}
          >
            <option value="simulation">模拟面试</option>
            <option value="practice">练习模式</option>
          </select>
        </div>

        <div style={fieldStyle}>
          <label style={labelStyle}>默认最大轮次</label>
          <input
            type="number"
            min={3}
            max={30}
            value={preferences.defaultMaxTurns}
            onChange={(e) => preferences.setDefaultMaxTurns(Number(e.target.value))}
            style={{ ...selectStyle, width: 100 }}
          />
        </div>

        <div style={fieldStyle}>
          <label style={labelStyle}>默认模型档位</label>
          <select
            value={preferences.defaultModelTier}
            onChange={(e) => preferences.setDefaultModelTier(e.target.value as ModelTier)}
            style={selectStyle}
          >
            {Object.entries(modelTierLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <p style={{ fontSize: "0.78rem", color: "#64748b", lineHeight: 1.6, marginTop: "0.4rem" }}>
            模型由平台统一配置，档位决定使用的模型能力：自动按任务路由，或固定使用某一档位。
          </p>
        </div>

        <div style={fieldStyle}>
          <label style={{ ...labelStyle, display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <input
              type="checkbox"
              checked={preferences.coachingEnabled}
              onChange={(e) => preferences.setCoachingEnabled(e.target.checked)}
            />
            启用教练建议
          </label>
        </div>
      </div>

      {/* Data */}
      <div style={sectionStyle}>
        <h3 style={sectionTitleStyle}>数据与隐私</h3>
        <p style={{ fontSize: "0.85rem", color: "#64748b", lineHeight: 1.6 }}>
          当前为本地开发环境，数据存储在本地数据库中。
          <br />
          认证与多用户功能将在后续版本中提供。
        </p>
      </div>
    </div>
  )
}

const sectionStyle: React.CSSProperties = {
  backgroundColor: "#fff",
  borderRadius: "12px",
  border: "1px solid #e2e8f0",
  padding: "1.5rem",
  marginBottom: "1rem",
}

const sectionTitleStyle: React.CSSProperties = {
  fontSize: "0.95rem",
  fontWeight: 600,
  color: "#334155",
  marginBottom: "1rem",
}

const fieldStyle: React.CSSProperties = { marginBottom: "1rem" }

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "0.85rem",
  fontWeight: 500,
  color: "#334155",
  marginBottom: "0.35rem",
}

const selectStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.5rem 0.75rem",
  borderRadius: "6px",
  border: "1px solid #e2e8f0",
  fontSize: "0.9rem",
  color: "#1e293b",
  backgroundColor: "#fff",
}
