import { useMemo, useState } from "react"
import type { AnswerVersion } from "@/lib/types/answer-diff"

type DiffKind = "same" | "added" | "removed"

interface DiffToken {
  text: string
  kind: DiffKind
}

/**
 * Token-level diff between two answer texts.
 * CJK characters are diffed at character granularity; latin words as whole words.
 */
function diffTokens(original: string, revised: string): DiffToken[] {
  const a = tokenize(original)
  const b = tokenize(revised)
  const m = a.length
  const n = b.length

  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array<number>(n + 1).fill(0))
  for (let i = m - 1; i >= 0; i--) {
    for (let j = n - 1; j >= 0; j--) {
      dp[i]![j] = a[i] === b[j] ? dp[i + 1]![j + 1]! + 1 : Math.max(dp[i + 1]![j]!, dp[i]![j + 1]!)
    }
  }

  const out: DiffToken[] = []
  let i = 0
  let j = 0
  while (i < m && j < n) {
    if (a[i] === b[j]) {
      out.push({ text: a[i]!, kind: "same" })
      i++
      j++
    } else if (dp[i + 1]![j]! >= dp[i]![j + 1]!) {
      out.push({ text: a[i]!, kind: "removed" })
      i++
    } else {
      out.push({ text: b[j]!, kind: "added" })
      j++
    }
  }
  while (i < m) {
    out.push({ text: a[i]!, kind: "removed" })
    i++
  }
  while (j < n) {
    out.push({ text: b[j]!, kind: "added" })
    j++
  }
  return out
}

function tokenize(text: string): string[] {
  return text.match(/[一-鿿]|[A-Za-z0-9]+|[^一-鿿\sA-Za-z0-9]|\s+/g) ?? []
}

function formatDate(value: string | null): string {
  if (!value) return "--"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`
}

export default function AnswerDiffViewer({ versions }: { versions: AnswerVersion[] }) {
  const [selectedIndex, setSelectedIndex] = useState(() => Math.max(0, versions.length - 1))
  const safeIndex = Math.min(selectedIndex, versions.length - 1)
  const current = versions[safeIndex]
  const previous = safeIndex > 0 ? versions[safeIndex - 1] : undefined

  const currentText = current?.answer_text ?? ""
  const previousText = previous?.answer_text ?? null
  const tokens = useMemo(
    () => (previousText != null ? diffTokens(previousText, currentText) : null),
    [previousText, currentText],
  )

  if (!current) return null
  const diff = current.diff

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={styles.titleRow}>
          <span style={styles.title}>作答版本对比</span>
          {versions.length > 1 ? (
            <span style={styles.versionCount}>共 {versions.length} 个版本</span>
          ) : null}
        </div>
        <div style={styles.tabs}>
          {versions.map((version, index) => {
            const active = index === safeIndex
            return (
              <button
                key={version.answer_id}
                type="button"
                onClick={() => setSelectedIndex(index)}
                style={{
                  ...styles.tab,
                  ...(active ? styles.tabActive : {}),
                }}
              >
                v{version.version_number}
              </button>
            )
          })}
        </div>
      </div>

      {versions.length > 1 && previous ? (
        <>
          <div style={styles.summaryRow}>
            <ScoreDelta current={current} previous={previous} />
            <ChangeRatio diff={diff} />
            <EvidenceFlag diff={diff} />
          </div>

          <div style={styles.diffBox}>
            <div style={styles.diffLegend}>
              <span style={styles.legendItem}>
                <span style={styles.legendAdd}>新增</span>
              </span>
              <span style={styles.legendItem}>
                <span style={styles.legendRemove}>删除</span>
              </span>
            </div>
            <div style={styles.diffText}>
              {tokens?.length ? (
                tokens.map((token, index) => (
                  <span
                    key={index}
                    style={
                      token.kind === "added"
                        ? styles.tokenAdded
                        : token.kind === "removed"
                          ? styles.tokenRemoved
                          : undefined
                    }
                  >
                    {token.text}
                  </span>
                ))
              ) : (
                currentText
              )}
            </div>
          </div>
        </>
      ) : null}

      <div style={styles.answerBox}>
        <div style={styles.answerLabel}>v{current.version_number} · {formatDate(current.created_at)}</div>
        <div style={styles.answerText}>{currentText || "（空回答）"}</div>
      </div>
    </div>
  )
}

function ScoreDelta({
  current,
  previous,
}: {
  current: AnswerVersion
  previous: AnswerVersion
}) {
  if (current.score == null || previous.score == null) {
    return <span style={styles.summaryPill}>评分：无逐版本数据</span>
  }
  const delta = Math.round((current.score - previous.score) * 10) / 10
  const arrow = delta > 0 ? "↑" : delta < 0 ? "↓" : "→"
  const color = delta > 0 ? "var(--wj-success)" : delta < 0 ? "var(--wj-error)" : "var(--wj-text-secondary)"
  return (
    <span style={styles.summaryPill}>
      <span style={styles.muted}>评分变化</span>{" "}
      <strong style={{ color }}>
        {previous.score} → {current.score} {arrow} {delta > 0 ? "+" : ""}{delta}
      </strong>
    </span>
  )
}

function ChangeRatio({ diff }: { diff: AnswerVersion["diff"] }) {
  if (!diff) return null
  const pct = Math.round(diff.change_ratio * 100)
  return (
    <span style={styles.summaryPill}>
      <span style={styles.muted}>变化比例</span> {pct}%
    </span>
  )
}

function EvidenceFlag({ diff }: { diff: AnswerVersion["diff"] }) {
  if (!diff) return null
  const badges: Array<{ label: string; tone: "good" | "warn" | "info" }> = []
  if (diff.new_evidence) badges.push({ label: "新增证据", tone: "good" })
  if (diff.is_substantive_change && !diff.coaching_repetition) {
    badges.push({ label: "实质改进", tone: "good" })
  }
  if (diff.coaching_repetition) badges.push({ label: "疑似复述反馈", tone: "warn" })
  if (!diff.new_evidence && !diff.is_substantive_change && !diff.coaching_repetition) {
    badges.push({ label: "改动有限", tone: "info" })
  }
  return (
    <span style={styles.badgeRow}>
      {badges.map((badge) => (
        <span
          key={badge.label}
          style={
            badge.tone === "good"
              ? styles.badgeGood
              : badge.tone === "warn"
                ? styles.badgeWarn
                : styles.badgeInfo
          }
        >
          {badge.label}
        </span>
      ))}
    </span>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "grid",
    gap: "0.75rem",
    padding: "0.9rem 1rem",
    backgroundColor: "var(--wj-bg-subtle)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.6rem",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "1rem",
    flexWrap: "wrap",
  },
  titleRow: { display: "flex", alignItems: "center", gap: "0.5rem" },
  title: { fontWeight: 600, color: "var(--wj-text-primary)", fontSize: "0.88rem" },
  versionCount: { fontSize: "0.75rem", color: "var(--wj-text-tertiary)" },
  tabs: { display: "flex", gap: "0.35rem" },
  tab: {
    padding: "0.2rem 0.6rem",
    borderRadius: "0.4rem",
    border: "1px solid var(--wj-border-default)",
    background: "var(--wj-bg-surface)",
    color: "var(--wj-text-secondary)",
    fontSize: "0.75rem",
    cursor: "pointer",
  },
  tabActive: {
    background: "var(--wj-brand-primary)",
    color: "#fff",
    borderColor: "var(--wj-brand-primary)",
  },
  summaryRow: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    flexWrap: "wrap",
  },
  summaryPill: {
    padding: "0.22rem 0.6rem",
    borderRadius: 999,
    background: "var(--wj-bg-surface)",
    border: "1px solid var(--wj-border-default)",
    fontSize: "0.76rem",
    color: "var(--wj-text-primary)",
  },
  muted: { color: "var(--wj-text-tertiary)" },
  badgeRow: { display: "flex", gap: "0.35rem", flexWrap: "wrap" },
  badgeGood: {
    padding: "0.22rem 0.6rem",
    borderRadius: 999,
    background: "var(--wj-success-bg)",
    color: "var(--wj-success)",
    fontSize: "0.76rem",
    fontWeight: 600,
  },
  badgeWarn: {
    padding: "0.22rem 0.6rem",
    borderRadius: 999,
    background: "var(--wj-warning-bg)",
    color: "var(--wj-warning)",
    fontSize: "0.76rem",
    fontWeight: 600,
  },
  badgeInfo: {
    padding: "0.22rem 0.6rem",
    borderRadius: 999,
    background: "var(--wj-bg-surface)",
    color: "var(--wj-text-secondary)",
    border: "1px solid var(--wj-border-default)",
    fontSize: "0.76rem",
  },
  diffBox: { display: "grid", gap: "0.4rem" },
  diffLegend: { display: "flex", gap: "0.75rem", fontSize: "0.72rem", color: "var(--wj-text-tertiary)" },
  legendItem: { display: "flex", alignItems: "center", gap: "0.25rem" },
  legendAdd: { padding: "0 0.3rem", borderRadius: "0.2rem", background: "rgba(22,163,74,0.14)", color: "#166534" },
  legendRemove: {
    padding: "0 0.3rem",
    borderRadius: "0.2rem",
    background: "rgba(220,38,38,0.12)",
    color: "#b91c1c",
    textDecoration: "line-through",
  },
  diffText: {
    whiteSpace: "pre-wrap",
    lineHeight: 1.75,
    color: "var(--wj-text-primary)",
    fontSize: "0.84rem",
    fontFamily: '"JetBrains Mono", Consolas, monospace',
  },
  tokenAdded: { backgroundColor: "rgba(22,163,74,0.14)", color: "#166534" },
  tokenRemoved: {
    backgroundColor: "rgba(220,38,38,0.12)",
    color: "#b91c1c",
    textDecoration: "line-through",
  },
  answerBox: {
    padding: "0.7rem 0.85rem",
    background: "var(--wj-bg-surface)",
    border: "1px solid var(--wj-border-default)",
    borderRadius: "0.5rem",
    display: "grid",
    gap: "0.35rem",
  },
  answerLabel: { fontSize: "0.72rem", color: "var(--wj-text-tertiary)" },
  answerText: { whiteSpace: "pre-wrap", lineHeight: 1.75, color: "var(--wj-text-secondary)", fontSize: "0.84rem" },
}
