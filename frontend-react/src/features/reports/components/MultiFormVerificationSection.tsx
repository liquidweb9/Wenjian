import React from "react"

interface QuestionFormCoverage {
  competency_code: string
  forms_used: string[]
  total_questions: number
  verification_depth: "SHALLOW" | "MODERATE" | "DEEP"
}

interface MultiFormVerificationSectionProps {
  formCoverageData: QuestionFormCoverage[]
}

/**
 * Multi-form Verification Section - Phase 2.2
 *
 * Displays question form coverage for competency verification:
 * - Which question forms were used for each competency
 * - Verification depth based on form diversity
 * - Recommendations for deeper verification
 */
export function MultiFormVerificationSection({
  formCoverageData,
}: MultiFormVerificationSectionProps) {
  if (!formCoverageData || formCoverageData.length === 0) {
    return (
      <div style={styles.emptyState}>
        <div style={styles.emptyIcon}>📋</div>
        <div style={styles.emptyTitle}>暂无多形式验证数据</div>
        <p style={styles.emptyText}>
          本次面试尚未使用多形式验证策略。多形式验证通过不同角度的提问（概念、项目细节、调试、反事实等）
          来全面评估能力的真实性和迁移性。
        </p>
      </div>
    )
  }

  const deepVerified = formCoverageData.filter(
    (item) => item.verification_depth === "DEEP"
  )
  const moderateVerified = formCoverageData.filter(
    (item) => item.verification_depth === "MODERATE"
  )
  const shallowVerified = formCoverageData.filter(
    (item) => item.verification_depth === "SHALLOW"
  )

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>多形式验证覆盖</h3>
        <p style={styles.subtitle}>
          通过不同问题形式验证能力的真实性和迁移性
        </p>
      </div>

      <div style={styles.statsGrid}>
        <StatCard
          label="深度验证"
          value={String(deepVerified.length)}
          description="使用 3+ 种问题形式"
          status="success"
        />
        <StatCard
          label="中度验证"
          value={String(moderateVerified.length)}
          description="使用 2 种问题形式"
          status="moderate"
        />
        <StatCard
          label="浅层验证"
          value={String(shallowVerified.length)}
          description="仅使用 1 种问题形式"
          status="shallow"
        />
        <StatCard
          label="总计能力"
          value={String(formCoverageData.length)}
          description="本次面试考察的能力数"
          status="info"
        />
      </div>

      <div style={styles.coverageList}>
        {formCoverageData.map((coverage, index) => (
          <div key={index} style={styles.coverageCard}>
            <div style={styles.coverageHeader}>
              <div style={styles.competencyInfo}>
                <span style={styles.competencyCode}>
                  {coverage.competency_code}
                </span>
                <span style={styles.questionCount}>
                  {coverage.total_questions} 个问题
                </span>
              </div>
              <span
                style={{
                  ...styles.depthBadge,
                  ...getDepthStyle(coverage.verification_depth),
                }}
              >
                {formatDepth(coverage.verification_depth)}
              </span>
            </div>

            <div style={styles.formsUsed}>
              <div style={styles.formsLabel}>使用的问题形式:</div>
              <div style={styles.formsList}>
                {coverage.forms_used.map((form, idx) => (
                  <span
                    key={idx}
                    style={{
                      ...styles.formBadge,
                      ...getFormStyle(form),
                    }}
                  >
                    {formatFormType(form)}
                  </span>
                ))}
              </div>
            </div>

            {coverage.verification_depth === "SHALLOW" && (
              <div style={styles.recommendationBox}>
                <span style={styles.recommendationIcon}>💡</span>
                <span style={styles.recommendationText}>
                  建议补充更多问题形式以提高验证可信度
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={styles.infoBox}>
        <div style={styles.infoTitle}>💡 关于多形式验证</div>
        <p style={styles.infoText}>
          多形式验证通过不同类型的问题考察同一能力：
        </p>
        <ul style={styles.infoList}>
          <li>
            <strong>概念题 (CONCEPT)</strong> - 验证理论理解
          </li>
          <li>
            <strong>项目细节 (PROJECT_DETAIL)</strong> - 验证实际经验
          </li>
          <li>
            <strong>调试题 (DEBUGGING)</strong> - 验证问题排查能力
          </li>
          <li>
            <strong>架构权衡 (ARCHITECTURE)</strong> - 验证设计思维
          </li>
          <li>
            <strong>反事实 (COUNTERFACTUAL)</strong> - 验证迁移能力
          </li>
        </ul>
        <p style={styles.infoText}>
          深度验证（3+ 形式）能更可靠地区分死记硬背和真实能力。
        </p>
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  description,
  status,
}: {
  label: string
  value: string
  description: string
  status: "success" | "moderate" | "shallow" | "info"
}) {
  return (
    <div style={styles.statCard}>
      <div style={styles.statLabel}>{label}</div>
      <div
        style={{
          ...styles.statValue,
          color: getStatusColor(status),
        }}
      >
        {value}
      </div>
      <div style={styles.statDescription}>{description}</div>
    </div>
  )
}

function getStatusColor(status: string): string {
  const colorMap: Record<string, string> = {
    success: "#16a34a",
    moderate: "#2563eb",
    shallow: "#ea580c",
    info: "#64748b",
  }
  return colorMap[status] || "#64748b"
}

function formatDepth(depth: string): string {
  const depthMap: Record<string, string> = {
    DEEP: "深度验证",
    MODERATE: "中度验证",
    SHALLOW: "浅层验证",
  }
  return depthMap[depth] || depth
}

function getDepthStyle(depth: string): React.CSSProperties {
  const styleMap: Record<string, React.CSSProperties> = {
    DEEP: {
      backgroundColor: "#f0fdf4",
      color: "#16a34a",
    },
    MODERATE: {
      backgroundColor: "#eff6ff",
      color: "#2563eb",
    },
    SHALLOW: {
      backgroundColor: "#fff7ed",
      color: "#ea580c",
    },
  }
  return (
    styleMap[depth] || {
      backgroundColor: "#f1f5f9",
      color: "#64748b",
    }
  )
}

function formatFormType(form: string): string {
  const formMap: Record<string, string> = {
    CONCEPT: "概念",
    PROJECT_DETAIL: "项目细节",
    DEBUGGING: "调试",
    ARCHITECTURE: "架构",
    COUNTERFACTUAL: "反事实",
    SCENARIO: "场景",
    SYSTEM_DESIGN: "系统设计",
  }
  return formMap[form] || form
}

function getFormStyle(form: string): React.CSSProperties {
  const styleMap: Record<string, React.CSSProperties> = {
    CONCEPT: {
      backgroundColor: "#dbeafe",
      color: "#1e40af",
    },
    PROJECT_DETAIL: {
      backgroundColor: "#dcfce7",
      color: "#15803d",
    },
    DEBUGGING: {
      backgroundColor: "#fed7aa",
      color: "#c2410c",
    },
    ARCHITECTURE: {
      backgroundColor: "#e9d5ff",
      color: "#7c3aed",
    },
    COUNTERFACTUAL: {
      backgroundColor: "#fce7f3",
      color: "#be185d",
    },
    SCENARIO: {
      backgroundColor: "#fef3c7",
      color: "#ca8a04",
    },
    SYSTEM_DESIGN: {
      backgroundColor: "#cffafe",
      color: "#0e7490",
    },
  }
  return (
    styleMap[form] || {
      backgroundColor: "#f1f5f9",
      color: "#64748b",
    }
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "grid",
    gap: "1.25rem",
  },
  header: {
    display: "grid",
    gap: "0.5rem",
  },
  title: {
    margin: 0,
    fontSize: "1.2rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
  },
  subtitle: {
    margin: 0,
    fontSize: "0.88rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.6,
  },
  emptyState: {
    padding: "2.5rem 1.5rem",
    textAlign: "center",
    backgroundColor: "var(--wj-bg-subtle)",
    borderRadius: "0.75rem",
  },
  emptyIcon: {
    fontSize: "3rem",
    marginBottom: "0.75rem",
  },
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
    maxWidth: 600,
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "1rem",
  },
  statCard: {
    padding: "1.25rem",
    backgroundColor: "var(--wj-bg-subtle)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.75rem",
    display: "grid",
    gap: "0.5rem",
  },
  statLabel: {
    fontSize: "0.8rem",
    fontWeight: 600,
    color: "var(--wj-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  statValue: {
    fontSize: "2rem",
    fontWeight: 700,
  },
  statDescription: {
    fontSize: "0.82rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.5,
  },
  coverageList: {
    display: "grid",
    gap: "0.75rem",
  },
  coverageCard: {
    padding: "1.25rem",
    backgroundColor: "var(--wj-bg-subtle)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.75rem",
    display: "grid",
    gap: "1rem",
  },
  coverageHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "1rem",
  },
  competencyInfo: {
    display: "flex",
    alignItems: "center",
    gap: "0.75rem",
  },
  competencyCode: {
    fontSize: "0.95rem",
    fontWeight: 600,
    color: "var(--wj-text-primary)",
    fontFamily: '"JetBrains Mono", Consolas, monospace',
  },
  questionCount: {
    fontSize: "0.8rem",
    color: "var(--wj-text-secondary)",
  },
  depthBadge: {
    padding: "0.25rem 0.75rem",
    borderRadius: 999,
    fontSize: "0.75rem",
    fontWeight: 600,
  },
  formsUsed: {
    display: "grid",
    gap: "0.5rem",
  },
  formsLabel: {
    fontSize: "0.8rem",
    fontWeight: 600,
    color: "var(--wj-text-secondary)",
  },
  formsList: {
    display: "flex",
    flexWrap: "wrap",
    gap: "0.5rem",
  },
  formBadge: {
    padding: "0.35rem 0.75rem",
    borderRadius: "0.375rem",
    fontSize: "0.8rem",
    fontWeight: 500,
  },
  recommendationBox: {
    display: "flex",
    gap: "0.5rem",
    padding: "0.75rem 1rem",
    backgroundColor: "var(--wj-info-bg)",
    border: "1px solid rgba(37, 99, 235, 0.2)",
    borderRadius: "0.5rem",
  },
  recommendationIcon: {
    fontSize: "1rem",
    flexShrink: 0,
  },
  recommendationText: {
    fontSize: "0.85rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.6,
  },
  infoBox: {
    padding: "1rem 1.25rem",
    backgroundColor: "var(--wj-info-bg)",
    border: "1px solid rgba(37, 99, 235, 0.2)",
    borderRadius: "0.75rem",
  },
  infoTitle: {
    margin: 0,
    marginBottom: "0.5rem",
    fontSize: "0.9rem",
    fontWeight: 600,
    color: "var(--wj-info)",
  },
  infoText: {
    margin: "0 0 0.5rem 0",
    fontSize: "0.85rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.7,
  },
  infoList: {
    margin: "0.5rem 0",
    paddingLeft: "1.5rem",
    fontSize: "0.85rem",
    color: "var(--wj-text-secondary)",
    lineHeight: 1.7,
  },
}
