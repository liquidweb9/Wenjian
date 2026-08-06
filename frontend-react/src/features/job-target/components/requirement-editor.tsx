import React, { useState } from "react"
import type { CompetencyCode, RequirementCreateRequest } from "@/lib/types/job-target"

interface RequirementEditorProps {
  requirements: RequirementCreateRequest[]
  onChange: (requirements: RequirementCreateRequest[]) => void
}

export function RequirementEditor({ requirements, onChange }: RequirementEditorProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null)

  const handleAdd = () => {
    setEditingIndex(requirements.length)
    onChange([
      ...requirements,
      {
        competency_code: "backend.language_runtime",
        title: "",
        importance: 0.8,
        expected_level: 3,
        evidence_expectation: ["", ""],
      },
    ])
  }

  const handleRemove = (index: number) => {
    onChange(requirements.filter((_, i) => i !== index))
    if (editingIndex === index) setEditingIndex(null)
  }

  const handleUpdate = (index: number, updated: Partial<RequirementCreateRequest>) => {
    onChange(requirements.map((req, i) => (i === index ? { ...req, ...updated } : req)))
  }

  const handleEvidenceChange = (reqIndex: number, evidenceIndex: number, value: string) => {
    const req = requirements[reqIndex]
    if (!req) return
    const newEvidence = [...req.evidence_expectation]
    newEvidence[evidenceIndex] = value
    handleUpdate(reqIndex, { evidence_expectation: newEvidence })
  }

  const handleAddEvidence = (reqIndex: number) => {
    const req = requirements[reqIndex]
    if (!req) return
    handleUpdate(reqIndex, { evidence_expectation: [...req.evidence_expectation, ""] })
  }

  const handleRemoveEvidence = (reqIndex: number, evidenceIndex: number) => {
    const req = requirements[reqIndex]
    if (!req) return
    if (req.evidence_expectation.length <= 2) return // Minimum 2 items
    handleUpdate(reqIndex, {
      evidence_expectation: req.evidence_expectation.filter((_, i) => i !== evidenceIndex),
    })
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>能力需求 ({requirements.length})</h3>
        <button onClick={handleAdd} style={styles.addButton}>
          + 添加需求
        </button>
      </div>

      {requirements.length === 0 ? (
        <div style={styles.emptyState}>暂无能力需求，点击"添加需求"开始配置</div>
      ) : (
        <div style={styles.list}>
          {requirements.map((req, index) => (
            <div key={index} style={styles.requirementCard}>
              <div style={styles.cardHeader}>
                <div style={styles.cardIndex}>#{index + 1}</div>
                <button
                  onClick={() => setEditingIndex(editingIndex === index ? null : index)}
                  style={styles.editButton}
                >
                  {editingIndex === index ? "收起" : "编辑"}
                </button>
                <button onClick={() => handleRemove(index)} style={styles.removeButton}>
                  删除
                </button>
              </div>

              {editingIndex === index ? (
                <div style={styles.editForm}>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>能力代码 *</label>
                    <select
                      value={req.competency_code}
                      onChange={(e) =>
                        handleUpdate(index, { competency_code: e.target.value as CompetencyCode })
                      }
                      style={styles.select}
                    >
                      <optgroup label="后端能力">
                        <option value="backend.language_runtime">语言与运行时</option>
                        <option value="backend.api_protocol">API 协议</option>
                        <option value="backend.database_modeling">数据库建模</option>
                        <option value="backend.transaction_consistency">事务一致性</option>
                        <option value="backend.cache">缓存设计</option>
                        <option value="backend.message_queue">消息队列</option>
                        <option value="backend.concurrency">并发处理</option>
                        <option value="backend.observability">可观测性</option>
                        <option value="backend.failure_recovery">故障恢复</option>
                        <option value="backend.security">安全防护</option>
                        <option value="backend.system_design">系统设计</option>
                        <option value="backend.testing">测试策略</option>
                        <option value="backend.delivery">交付流程</option>
                      </optgroup>
                      <optgroup label="AI Agent 能力">
                        <option value="agent.prompt_design">Prompt 工程</option>
                        <option value="agent.structured_output">结构化输出</option>
                        <option value="agent.workflow_orchestration">工作流编排</option>
                        <option value="agent.state_management">状态管理</option>
                        <option value="agent.tool_calling">Tool Calling</option>
                        <option value="agent.rag_fundamentals">RAG 基础</option>
                        <option value="agent.eval">Eval 与测试</option>
                        <option value="agent.guardrail">Guardrail 设计</option>
                        <option value="agent.cost_latency">成本延迟优化</option>
                        <option value="agent.production_reliability">生产可靠性</option>
                      </optgroup>
                    </select>
                  </div>

                  <div style={styles.formGroup}>
                    <label style={styles.label}>需求标题 *</label>
                    <input
                      type="text"
                      value={req.title}
                      onChange={(e) => handleUpdate(index, { title: e.target.value })}
                      placeholder="例如：Java 语言与 JVM"
                      style={styles.input}
                    />
                  </div>

                  <div style={styles.formGroup}>
                    <label style={styles.label}>详细描述</label>
                    <textarea
                      value={req.description || ""}
                      onChange={(e) => handleUpdate(index, { description: e.target.value })}
                      placeholder="详细描述此能力的要求..."
                      style={styles.textarea}
                    />
                  </div>

                  <div style={styles.formRow}>
                    <div style={styles.formGroup}>
                      <label style={styles.label}>重要度 (0-1) *</label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.05"
                        value={req.importance}
                        onChange={(e) =>
                          handleUpdate(index, { importance: parseFloat(e.target.value) || 0 })
                        }
                        style={styles.input}
                      />
                    </div>

                    <div style={styles.formGroup}>
                      <label style={styles.label}>期望水平 (1-5) *</label>
                      <input
                        type="number"
                        min="1"
                        max="5"
                        value={req.expected_level}
                        onChange={(e) =>
                          handleUpdate(index, { expected_level: parseInt(e.target.value) || 1 })
                        }
                        style={styles.input}
                      />
                    </div>
                  </div>

                  <div style={styles.formGroup}>
                    <label style={styles.label}>证据期望 (至少2条) *</label>
                    {req.evidence_expectation.map((evidence, evidenceIndex) => (
                      <div key={evidenceIndex} style={styles.evidenceRow}>
                        <input
                          type="text"
                          value={evidence}
                          onChange={(e) => handleEvidenceChange(index, evidenceIndex, e.target.value)}
                          placeholder={`证据期望 ${evidenceIndex + 1}`}
                          style={styles.evidenceInput}
                        />
                        {req.evidence_expectation.length > 2 && (
                          <button
                            onClick={() => handleRemoveEvidence(index, evidenceIndex)}
                            style={styles.removeEvidenceButton}
                          >
                            ×
                          </button>
                        )}
                      </div>
                    ))}
                    <button onClick={() => handleAddEvidence(index)} style={styles.addEvidenceButton}>
                      + 添加证据期望
                    </button>
                  </div>
                </div>
              ) : (
                <div style={styles.summary}>
                  <div style={styles.summaryTitle}>{req.title || "(未命名)"}</div>
                  <div style={styles.summaryMeta}>
                    <span style={styles.metaItem}>
                      重要度: {(req.importance * 100).toFixed(0)}%
                    </span>
                    <span style={styles.metaItem}>期望水平: {req.expected_level}</span>
                    <span style={styles.metaItem}>
                      {req.evidence_expectation.length} 条证据期望
                    </span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    marginTop: "24px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "16px",
  },
  title: {
    fontSize: "18px",
    fontWeight: 600,
    color: "#1a1a1a",
    margin: 0,
  },
  addButton: {
    padding: "8px 16px",
    backgroundColor: "#2563eb",
    color: "#ffffff",
    border: "none",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: 500,
    cursor: "pointer",
  },
  emptyState: {
    padding: "40px 20px",
    textAlign: "center",
    color: "#9ca3af",
    fontSize: "14px",
    backgroundColor: "#f9fafb",
    borderRadius: "8px",
    border: "1px dashed #d1d5db",
  },
  list: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  requirementCard: {
    padding: "16px",
    backgroundColor: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
  },
  cardHeader: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "12px",
  },
  cardIndex: {
    fontSize: "13px",
    fontWeight: 600,
    color: "#6b7280",
  },
  editButton: {
    padding: "6px 12px",
    backgroundColor: "#f3f4f6",
    color: "#374151",
    border: "none",
    borderRadius: "6px",
    fontSize: "12px",
    fontWeight: 500,
    cursor: "pointer",
    marginLeft: "auto",
  },
  removeButton: {
    padding: "6px 12px",
    backgroundColor: "#fee2e2",
    color: "#991b1b",
    border: "none",
    borderRadius: "6px",
    fontSize: "12px",
    fontWeight: 500,
    cursor: "pointer",
  },
  editForm: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  formGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  formRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "16px",
  },
  label: {
    fontSize: "13px",
    fontWeight: 500,
    color: "#374151",
  },
  input: {
    padding: "8px 12px",
    fontSize: "14px",
    border: "1px solid #d1d5db",
    borderRadius: "6px",
  },
  select: {
    padding: "8px 12px",
    fontSize: "14px",
    border: "1px solid #d1d5db",
    borderRadius: "6px",
    backgroundColor: "#ffffff",
  },
  textarea: {
    padding: "8px 12px",
    fontSize: "14px",
    border: "1px solid #d1d5db",
    borderRadius: "6px",
    resize: "vertical",
    minHeight: "60px",
    fontFamily: "inherit",
  },
  evidenceRow: {
    display: "flex",
    gap: "8px",
    alignItems: "center",
  },
  evidenceInput: {
    flex: 1,
    padding: "8px 12px",
    fontSize: "13px",
    border: "1px solid #d1d5db",
    borderRadius: "6px",
  },
  removeEvidenceButton: {
    width: "28px",
    height: "28px",
    padding: 0,
    backgroundColor: "#fee2e2",
    color: "#991b1b",
    border: "none",
    borderRadius: "6px",
    fontSize: "18px",
    fontWeight: 600,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  addEvidenceButton: {
    padding: "6px 12px",
    backgroundColor: "#f3f4f6",
    color: "#374151",
    border: "none",
    borderRadius: "6px",
    fontSize: "12px",
    fontWeight: 500,
    cursor: "pointer",
    width: "fit-content",
  },
  summary: {
    paddingLeft: "8px",
  },
  summaryTitle: {
    fontSize: "15px",
    fontWeight: 600,
    color: "#1a1a1a",
    marginBottom: "8px",
  },
  summaryMeta: {
    display: "flex",
    gap: "16px",
    fontSize: "13px",
    color: "#6b7280",
  },
  metaItem: {
    display: "inline-block",
  },
}
