import { useCallback, useEffect, useRef, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { ArrowLeft, BrainCircuit, CheckCircle2, FileSearch, LoaderCircle, ShieldCheck, Sparkles } from "lucide-react"
import { BrandLogo } from "@/components/brand/BrandLogo"
import { BackButton } from "@/components/common/back-button"
import { useInterviewStream } from "../hooks/use-interview-stream"
import { useFinishInterview, useInterview, useSubmitAnswer } from "../hooks/use-interviews"
import { useInterviewDraftStore } from "@/stores/interview-draft-store"
import { usePageTitle } from "@/lib/use-page-title"
import { useAnswerVersions } from "@/features/answer-diff/hooks/use-answer-diff"
import AnswerDiffViewer from "@/features/answer-diff/components/answer-diff-viewer"
import type { ConnectionState, InterviewStage } from "../runtime/event-schema"

const stageMessages: Record<InterviewStage, string> = {
  loading: "问鉴正在载入当前面试。",
  connecting: "正在连接实时面试通道。",
  waiting_for_question: "正在结合简历证据生成下一轮问题。",
  answering: "请围绕当前问题给出你的回答。",
  submitting: "问鉴正在提交你的回答。",
  analyzing: "问鉴正在分析你的回答，并评估与简历陈述的一致性。",
  question_ready: "新问题已准备好。",
  finishing: "正在结束面试并准备报告。",
  finished: "本场面试已完成。",
  error: "当前面试流程出现异常。",
}

const connectionLabels: Record<ConnectionState, string> = {
  idle: "空闲",
  connecting: "连接中",
  connected: "已连接",
  reconnecting: "自动重连中",
  disconnected: "连接已断开",
  failed: "连接失败",
}

const DIMENSION_WEIGHTS: Record<string, number> = {
  technical_correctness: 25,
  implementation_depth: 20,
  architecture_tradeoffs: 15,
  personal_contribution: 15,
  production_awareness: 15,
  clarity: 10,
}

interface HistoryEntry {
  q: string
  a: string
  questionId?: string
  evaluation?: Record<string, unknown> | null
  coaching?: Record<string, unknown> | null
}

export default function InterviewRoomPage() {
  const { interviewId } = useParams<{ interviewId: string }>()
  const navigate = useNavigate()
  usePageTitle("", "模拟面试进行中")

  const { data: interview } = useInterview(interviewId)
  const runtime = useInterviewStream(interviewId, interview?.current_question)
  const submitAnswer = useSubmitAnswer()
  const finishInterview = useFinishInterview()

  const drafts = useInterviewDraftStore((state) => state.drafts)
  const pendingSubmissions = useInterviewDraftStore((state) => state.pendingSubmissions)
  const setDraft = useInterviewDraftStore((state) => state.setDraft)
  const clearDraft = useInterviewDraftStore((state) => state.clearDraft)
  const setPendingSubmission = useInterviewDraftStore((state) => state.setPendingSubmission)
  const clearPendingSubmission = useInterviewDraftStore((state) => state.clearPendingSubmission)

  const [answer, setAnswer] = useState("")
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [selectedHistoryIdx, setSelectedHistoryIdx] = useState<number | null>(null)
  const [lastSubmissionKey, setLastSubmissionKey] = useState("")

  const previousQuestionId = useRef<string | null>(null)
  const prevEvalRef = useRef<Record<string, unknown> | null>(null)
  const prevCoachingRef = useRef<Record<string, unknown> | null>(null)

  const questionId = runtime.currentQuestion?.question_id as string | undefined
  const currentQuestionText = runtime.currentQuestion?.question_text as string | undefined
  const pendingSubmissionKey =
    interviewId && questionId ? pendingSubmissions[`${interviewId}_${questionId}`] : undefined

  useEffect(() => {
    if (questionId && questionId !== previousQuestionId.current) {
      previousQuestionId.current = questionId
      const draftKey = `${interviewId}_${questionId}`
      const savedDraft = drafts[draftKey]
      setAnswer(typeof savedDraft === "string" ? savedDraft : "")
    }
  }, [questionId, interviewId, drafts])

  useEffect(() => {
    if (!interview?.history) return

    // Polling may first return a question while its long-running answer is not
    // persisted yet. Reconcile every snapshot instead of freezing that first,
    // incomplete history response for the lifetime of the page.
    setHistory((current) => {
      const localByQuestion = new Map(
        current
          .filter((entry) => entry.questionId)
          .map((entry) => [entry.questionId!, entry]),
      )
      const serverQuestionIds = new Set(interview.history.map((entry) => entry.question_id))
      const reconciled = interview.history.map((entry) => {
        const local = localByQuestion.get(entry.question_id)
        return {
          q: entry.question_text,
          a: entry.answer_text || local?.a || "",
          questionId: entry.question_id,
          evaluation: entry.evaluation || local?.evaluation || null,
          coaching: entry.coaching || local?.coaching || null,
        }
      })
      // Keep the optimistic latest turn until the server snapshot catches up.
      return [
        ...reconciled,
        ...current.filter(
          (entry) => entry.questionId && !serverQuestionIds.has(entry.questionId),
        ),
      ]
    })
  }, [interview?.history])

  useEffect(() => {
    if (!interviewId || !interview?.history?.length) return
    for (const entry of interview.history) {
      if (entry.question_id && entry.answer_text) {
        clearPendingSubmission(interviewId, entry.question_id)
      }
    }
  }, [clearPendingSubmission, interview?.history, interviewId])

  useEffect(() => {
    if (pendingSubmissionKey) setLastSubmissionKey(pendingSubmissionKey)
  }, [pendingSubmissionKey])

  useEffect(() => {
    // A completed backend request can advance through SSE after Axios has already
    // timed out. Do not carry that stale mutation error onto the new question.
    submitAnswer.reset()
    // reset is stable for the mutation instance; only a question change should
    // clear the previous request state.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questionId])

  useEffect(() => {
    if (runtime.latestEvaluation && runtime.latestEvaluation !== prevEvalRef.current) {
      prevEvalRef.current = runtime.latestEvaluation
      setHistory((prev) => {
        if (!prev.length) return prev
        const next = [...prev]
        next[next.length - 1] = { ...next[next.length - 1]!, evaluation: runtime.latestEvaluation }
        return next
      })
    }
  }, [runtime.latestEvaluation])

  useEffect(() => {
    if (runtime.latestCoaching && runtime.latestCoaching !== prevCoachingRef.current) {
      prevCoachingRef.current = runtime.latestCoaching
      setHistory((prev) => {
        if (!prev.length) return prev
        const next = [...prev]
        next[next.length - 1] = { ...next[next.length - 1]!, coaching: runtime.latestCoaching }
        return next
      })
    }
  }, [runtime.latestCoaching])

  useEffect(() => {
    if (runtime.currentStage === "analyzing" && currentQuestionText && answer.trim()) {
      const lastEntry = history[history.length - 1]
      if (!lastEntry || lastEntry.q !== currentQuestionText) {
        prevEvalRef.current = null
        prevCoachingRef.current = null
        setHistory((prev) => [
          ...prev,
          {
            q: currentQuestionText,
            a: answer.trim(),
            questionId,
          },
        ])
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runtime.currentStage])

  useEffect(() => {
    if (runtime.currentStage === "answering") {
      setSelectedHistoryIdx(null)
    }
  }, [runtime.currentStage])

  const handleSubmit = useCallback(async () => {
    if (!interviewId || !questionId || !answer.trim()) return

    const idempotencyKey = pendingSubmissionKey || `${interviewId}_${questionId}_${crypto.randomUUID()}`
    setLastSubmissionKey(idempotencyKey)
    setDraft(interviewId, questionId, answer)
    setPendingSubmission(interviewId, questionId, idempotencyKey)

    try {
      await submitAnswer.mutateAsync({
        interviewId,
        questionId,
        answerText: answer.trim(),
        idempotencyKey,
      })
      clearDraft(interviewId, questionId)
      clearPendingSubmission(interviewId, questionId)
    } catch {
      // mutation state surfaces the error
    }
  }, [answer, clearDraft, clearPendingSubmission, interviewId, pendingSubmissionKey, questionId, setDraft, setPendingSubmission, submitAnswer])

  const handleFinish = useCallback(async () => {
    if (!interviewId) return
    await finishInterview.mutateAsync(interviewId)
  }, [finishInterview, interviewId])

  const stage = runtime.currentStage
  const isTransitioning =
    stage === "loading" ||
    runtime.connection === "connecting" ||
    runtime.connection === "reconnecting"
  const isFinished = stage === "finished" || stage === "finishing"
  const isAnalyzing = stage === "analyzing" || stage === "submitting"
  const isRecoveringSubmission = Boolean(pendingSubmissionKey)
  const currentTurn = (interview?.turn_count ?? 0) + 1

  return (
    <div style={{ minHeight: "100vh", background: "var(--wj-bg-page)" }}>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "1rem",
          padding: "1rem 1.35rem",
          background: "rgb(255 255 255 / 88%)",
          backdropFilter: "blur(16px)",
          borderBottom: "1px solid var(--wj-border-default)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.95rem" }}>
          <BackButton to="/app/interviews" label="返回记录" />
          <BrandLogo linkTo="/app/interviews" size={38} />
          <div>
            <div className="app-eyebrow">模拟面试</div>
            <div style={{ marginTop: "0.25rem", color: "var(--wj-text-primary)", fontWeight: 600 }}>
              第 {currentTurn} / {interview?.max_turns ?? "?"} 题
            </div>
          </div>
          <span
            style={{
              padding: "0.25rem 0.65rem",
              borderRadius: 999,
              background:
                runtime.connection === "connected"
                  ? "var(--wj-success-bg)"
                  : runtime.connection === "reconnecting"
                    ? "var(--wj-warning-bg)"
                    : runtime.connection === "failed"
                      ? "var(--wj-error-bg)"
                      : "var(--wj-bg-subtle)",
              color:
                runtime.connection === "connected"
                  ? "var(--wj-success)"
                  : runtime.connection === "reconnecting"
                    ? "var(--wj-warning)"
                    : runtime.connection === "failed"
                      ? "var(--wj-error)"
                      : "var(--wj-text-secondary)",
              fontSize: "0.78rem",
              fontWeight: 600,
            }}
          >
            {connectionLabels[runtime.connection]}
          </span>
        </div>

        <div style={{ display: "flex", gap: "0.65rem" }}>
          {!isFinished ? (
            <button type="button" className="btn-danger" disabled={finishInterview.isPending} onClick={handleFinish}>
              {finishInterview.isPending ? "正在结束…" : "结束面试"}
            </button>
          ) : null}
        </div>
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "280px minmax(0, 1fr) 320px",
          gap: "1rem",
          padding: "1rem",
          minHeight: "calc(100vh - 74px)",
        }}
      >
        <aside className="app-surface" style={{ padding: "1rem", display: "grid", alignContent: "start", gap: "1rem" }}>
          <div>
            <div className="app-eyebrow">Interview Context</div>
            <h2 style={{ margin: "0.45rem 0 0", fontSize: "1rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
              面试上下文
            </h2>
            <p style={{ margin: "0.45rem 0 0", color: "var(--wj-text-secondary)", fontSize: "0.84rem", lineHeight: 1.65 }}>
              {stageMessages[stage]}
            </p>
          </div>

          <div className="app-muted-surface" style={{ padding: "0.9rem 1rem" }}>
            <StatusRow label="目标岗位" value={interview?.target_role || "未指定"} />
            <StatusRow label="面试模式" value={interview?.mode === "practice" ? "练习模式" : "模拟面试"} />
            <StatusRow label="进度" value={`第 ${currentTurn} / ${interview?.max_turns ?? "?"} 题`} />
            <StatusRow label="连接状态" value={connectionLabels[runtime.connection]} />
          </div>

          {runtime.currentQuestion ? (
            <div className="app-muted-surface" style={{ padding: "0.9rem 1rem" }}>
              <h3 style={{ margin: 0, fontSize: "0.88rem", fontWeight: 600, color: "var(--wj-text-primary)", marginBottom: "0.6rem" }}>
                当前验证目标
              </h3>
              <StatusRow
                label="问题类型"
                value={(runtime.currentQuestion.question_form as string) || "概念理解"}
              />
              <StatusRow
                label="验证点"
                value={(runtime.currentQuestion.verification_point as string) || "简历陈述一致性"}
              />
              <StatusRow
                label="考察深度"
                value={`L${(runtime.currentQuestion.target_depth as number) || currentTurn}`}
              />
            </div>
          ) : null}

          <div>
            <h3 style={{ margin: 0, fontSize: "0.9rem", color: "var(--wj-text-primary)" }}>问答记录</h3>
            <p style={{ margin: "0.35rem 0 0", color: "var(--wj-text-secondary)", fontSize: "0.8rem", lineHeight: 1.6 }}>
              选择任一题目，可查看对应的评分与教练建议。
            </p>
            <div style={{ display: "grid", gap: "0.55rem", marginTop: "0.85rem" }}>
              {history.length ? (
                history.map((entry, index) => {
                  const selected = selectedHistoryIdx === index
                  return (
                    <button
                      key={`${entry.questionId}-${index}`}
                      type="button"
                      onClick={() => setSelectedHistoryIdx(selected ? null : index)}
                      style={{
                        textAlign: "left",
                        padding: "0.8rem 0.85rem",
                        borderRadius: 14,
                        border: selected ? "1px solid rgba(14,149,144,0.42)" : "1px solid var(--wj-border-default)",
                        background: selected ? "var(--wj-brand-accent-bg)" : "var(--wj-bg-surface)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", gap: "0.6rem", alignItems: "center" }}>
                        <span style={{ color: "var(--wj-brand-secondary)", fontSize: "0.78rem", fontWeight: 700 }}>
                          Q{index + 1}
                        </span>
                        {entry.evaluation ? <ScorePill evaluation={entry.evaluation} /> : null}
                      </div>
                      <div style={{ marginTop: "0.4rem", color: "var(--wj-text-secondary)", fontSize: "0.82rem", lineHeight: 1.55 }}>
                        {entry.q.length > 54 ? `${entry.q.slice(0, 54)}…` : entry.q}
                      </div>
                    </button>
                  )
                })
              ) : (
                <div className="app-muted-surface" style={{ padding: "0.85rem 0.95rem", color: "var(--wj-text-secondary)", fontSize: "0.82rem" }}>
                  当前还没有历史问答。第一题出现后，这里会逐步形成可回看的训练链路。
                </div>
              )}
            </div>
          </div>
        </aside>

        <main className="app-surface" style={{ padding: 0, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          {selectedHistoryIdx != null && history[selectedHistoryIdx] ? (
            <HistoryDetail
              interviewId={interviewId!}
              entry={history[selectedHistoryIdx]!}
              index={selectedHistoryIdx}
              onBack={() => setSelectedHistoryIdx(null)}
            />
          ) : null}

          {selectedHistoryIdx == null && isTransitioning ? (
            <CenteredStatus message={stageMessages[stage]} mode="connecting" />
          ) : null}

          {selectedHistoryIdx == null && !isTransitioning && stage === "waiting_for_question" ? (
            <CenteredStatus message="问鉴正在结合你的简历证据与前序回答，生成下一轮深度追问。" mode="question" />
          ) : null}

          {selectedHistoryIdx == null && !isTransitioning && (stage === "answering" || stage === "submitting") && currentQuestionText && !isRecoveringSubmission ? (
            <>
              <section style={{ padding: "1.4rem 1.5rem 1rem", borderBottom: "1px solid var(--wj-border-subtle)" }}>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap", marginBottom: "0.5rem" }}>
                  <div className="app-eyebrow">Current Question</div>
                  {runtime.currentQuestion?.question_form ? (
                    <span
                      style={{
                        padding: "0.2rem 0.6rem",
                        borderRadius: 999,
                        background: "var(--wj-brand-accent-bg)",
                        color: "var(--wj-brand-secondary)",
                        fontSize: "0.72rem",
                        fontWeight: 700,
                        textTransform: "uppercase",
                        letterSpacing: "0.03em",
                      }}
                    >
                      {formatQuestionForm(runtime.currentQuestion.question_form as string)}
                    </span>
                  ) : null}
                  {runtime.currentQuestion?.is_clarification ? (
                    <span
                      style={{
                        padding: "0.2rem 0.6rem",
                        borderRadius: 999,
                        background: "var(--wj-warning-bg)",
                        color: "var(--wj-warning)",
                        fontSize: "0.72rem",
                        fontWeight: 700,
                      }}
                    >
                      澄清模式
                    </span>
                  ) : null}
                  {runtime.currentQuestion?.is_counterfactual ? (
                    <span
                      style={{
                        padding: "0.2rem 0.6rem",
                        borderRadius: 999,
                        background: "var(--wj-info-bg)",
                        color: "var(--wj-info)",
                        fontSize: "0.72rem",
                        fontWeight: 700,
                      }}
                    >
                      反事实
                    </span>
                  ) : null}
                </div>
                <h1 style={{ margin: "0.35rem 0 0", fontSize: "1.55rem", lineHeight: 1.45, fontWeight: 600, color: "var(--wj-text-primary)" }}>
                  {currentQuestionText}
                </h1>
                <p style={{ margin: "0.65rem 0 0", color: "var(--wj-text-secondary)", lineHeight: 1.7 }}>
                  请优先回答事实、范围、角色与结果，必要时补充细节，让问鉴更好地评估回答与简历陈述的一致性。
                </p>
              </section>

              <section style={{ padding: "1.2rem 1.5rem 1.5rem", display: "grid", alignContent: "start", gap: "0.9rem", flex: 1 }}>
                <label style={{ display: "grid", gap: "0.5rem" }}>
                  <span style={{ fontWeight: 600, color: "var(--wj-text-primary)" }}>你的回答</span>
                  <textarea
                    value={answer}
                    onChange={(event) => {
                      setAnswer(event.target.value)
                      if (questionId && interviewId) {
                        setDraft(interviewId, questionId, event.target.value)
                      }
                    }}
                    disabled={stage === "submitting" || submitAnswer.isPending}
                    placeholder="从真实经历出发，描述背景、动作、决策依据和结果。"
                    style={{
                      width: "100%",
                      height: 180,
                      minHeight: 140,
                      maxHeight: "45vh",
                      resize: "vertical",
                      padding: "1rem",
                      borderRadius: 16,
                      border: "1px solid var(--wj-border-default)",
                      background: stage === "submitting" ? "var(--wj-bg-subtle)" : "var(--wj-bg-surface)",
                      color: "var(--wj-text-primary)",
                      lineHeight: 1.7,
                    }}
                  />
                </label>

                {submitAnswer.isError ? (
                  <div style={{ color: "var(--wj-error)", fontSize: "0.82rem" }}>
                    {(submitAnswer.error as Error)?.message || "回答提交失败，请稍后重试。"}
                  </div>
                ) : null}

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}>
                  <div style={{ color: "var(--wj-text-secondary)", fontSize: "0.8rem" }}>
                    {questionId ? `草稿会按题目自动保存。` : "当前题目加载后可开始作答。"}
                  </div>
                  <button
                    type="button"
                    className="btn-primary"
                    disabled={stage === "submitting" || submitAnswer.isPending || !answer.trim()}
                    onClick={handleSubmit}
                  >
                    {stage === "submitting" || submitAnswer.isPending ? "提交中…" : "提交回答"}
                  </button>
                </div>
              </section>
            </>
          ) : null}

          {selectedHistoryIdx == null && !isTransitioning && (isAnalyzing || isRecoveringSubmission) && stage !== "submitting" ? (
            <section style={{ padding: "1.6rem 1.5rem", overflow: "auto" }}>
              <AnalysisProgress
                hasAnalysis={Boolean(runtime.latestAnalysis)}
                hasEvaluation={Boolean(runtime.latestEvaluation)}
                hasEvidence={runtime.evidenceUpdated}
                hasCoaching={Boolean(runtime.latestCoaching)}
                submissionKey={lastSubmissionKey}
              />

              {runtime.latestEvaluation ? (
                <Panel title="本题评分" style={{ marginTop: "1rem" }}>
                  <ScoreDisplay evaluation={runtime.latestEvaluation} />
                </Panel>
              ) : null}

              {runtime.latestCoaching ? (
                <Panel title="反馈与改进建议" style={{ marginTop: "1rem" }}>
                  <CoachingDisplay coaching={runtime.latestCoaching} />
                </Panel>
              ) : null}
            </section>
          ) : null}

          {selectedHistoryIdx == null && isFinished ? (
            <div style={{ display: "grid", placeItems: "center", padding: "3rem 1.5rem", textAlign: "center", flex: 1 }}>
              <div>
                <div
                  style={{
                    width: 72,
                    height: 72,
                    margin: "0 auto",
                    borderRadius: 999,
                    background: "var(--wj-success-bg)",
                    color: "var(--wj-success)",
                    display: "grid",
                    placeItems: "center",
                  }}
                >
                  <CheckCircle2 size={34} />
                </div>
                <h2 style={{ margin: "1rem 0 0", color: "var(--wj-text-primary)", fontSize: "1.45rem", fontWeight: 600 }}>
                  本场面试已完成
                </h2>
                <p style={{ margin: "0.6rem auto 0", maxWidth: 460, color: "var(--wj-text-secondary)", lineHeight: 1.7 }}>
                  问鉴已经整理好本次回答评分、能力表现、证据一致性与后续训练建议。你现在可以进入报告页继续查看。
                </p>
                <button
                  type="button"
                  className="btn-primary"
                  style={{ marginTop: "1.4rem" }}
                  onClick={() => navigate(`/app/interviews/${interviewId}/report`)}
                >
                  查看面试报告
                </button>
              </div>
            </div>
          ) : null}

          {selectedHistoryIdx == null && stage === "error" ? (
            <div style={{ display: "grid", placeItems: "center", padding: "3rem 1.5rem", textAlign: "center", flex: 1 }}>
              <div>
                <h2 style={{ color: "var(--wj-text-primary)", fontSize: "1.3rem", fontWeight: 600 }}>本次分析未能完成</h2>
                <p style={{ margin: "0.6rem auto 0", maxWidth: 420, color: "var(--wj-text-secondary)", lineHeight: 1.7 }}>
                  {runtime.lastError || "你的面试和回答数据不会因此丢失，请重新尝试。"}
                </p>
                <button type="button" className="btn-primary" style={{ marginTop: "1.25rem" }} onClick={() => window.location.reload()}>
                  重新加载
                </button>
              </div>
            </div>
          ) : null}
        </main>

        <aside className="app-surface" style={{ padding: "1rem", display: "grid", alignContent: "start", gap: "1rem" }}>
          <div>
            <div className="app-eyebrow">Runtime</div>
            <h2 style={{ margin: "0.45rem 0 0", fontSize: "1rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
              当前运行状态
            </h2>
          </div>

          <div className="app-muted-surface" style={{ padding: "0.95rem 1rem" }}>
            <StatusRow label="连接状态" value={connectionLabels[runtime.connection]} />
            <StatusRow label="阶段提示" value={stageMessages[stage]} />
            <StatusRow label="目标岗位" value={interview?.target_role || "未指定"} />
          </div>

          <Panel title="追问策略">
            <p style={{ margin: 0, color: "var(--wj-text-secondary)", lineHeight: 1.7, fontSize: "0.85rem" }}>
              信息不足、实现细节偏浅或存在矛盾时会继续深挖；当前项目证据已充分、达到该项目追问上限，或其他项目优先级更高时会切换项目。总轮次只是上限，不是固定脚本。
            </p>
          </Panel>

          <Panel title="草稿与恢复">
            <p style={{ margin: 0, color: "var(--wj-text-secondary)", lineHeight: 1.7, fontSize: "0.85rem" }}>
              草稿按题保存。刷新或退出重进后会从服务端恢复当前问题与历史记录；分析仍在服务端继续，页面会通过实时连接和轮询补回结果，请勿重复提交同一题。
            </p>
          </Panel>
        </aside>
      </div>
    </div>
  )
}

function Panel({
  title,
  children,
  style,
}: {
  title: string
  children: React.ReactNode
  style?: React.CSSProperties
}) {
  return (
    <section className="app-muted-surface" style={{ padding: "0.95rem 1rem", ...style }}>
      <h3 style={{ margin: 0, fontSize: "0.9rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>{title}</h3>
      <div style={{ marginTop: "0.7rem" }}>{children}</div>
    </section>
  )
}

function HistoryDetail({
  interviewId,
  entry,
  index,
  onBack,
}: {
  interviewId: string
  entry: HistoryEntry
  index: number
  onBack: () => void
}) {
  const { data: versionsData } = useAnswerVersions(interviewId, entry.questionId)
  const versions = versionsData?.versions ?? []

  return (
    <div style={{ padding: "1.5rem", overflow: "auto", flex: 1 }}>
      <button type="button" className="btn-secondary" onClick={onBack}>
        <ArrowLeft size={16} />
        返回当前问题
      </button>
      <div style={{ marginTop: "1rem", display: "grid", gap: "1rem" }}>
        <Panel title={`Q${index + 1} 问题`}>
          <p style={{ margin: 0, color: "var(--wj-text-primary)", lineHeight: 1.75 }}>{entry.q}</p>
        </Panel>
        <Panel title="你的回答">
          <p style={{ margin: 0, color: "var(--wj-text-secondary)", lineHeight: 1.75, whiteSpace: "pre-wrap" }}>
            {entry.a || "本题尚未记录回答。"}
          </p>
        </Panel>
        {versions.length >= 2 ? (
          <Panel title="版本对比">
            <AnswerDiffViewer versions={versions} />
          </Panel>
        ) : null}
        {entry.evaluation ? (
          <Panel title="评分结果">
            <ScoreDisplay evaluation={entry.evaluation} />
          </Panel>
        ) : null}
        {entry.coaching ? (
          <Panel title="改进建议">
            <CoachingDisplay coaching={entry.coaching} />
          </Panel>
        ) : null}
      </div>
    </div>
  )
}

function CenteredStatus({
  message,
  mode,
}: {
  message: string
  mode: "connecting" | "question"
}) {
  const [seconds, setSeconds] = useState(0)

  useEffect(() => {
    const startedAt = Date.now()
    const timer = window.setInterval(() => setSeconds(Math.floor((Date.now() - startedAt) / 1000)), 1_000)
    return () => window.clearInterval(timer)
  }, [])

  const steps =
    mode === "question"
      ? ["读取项目上下文", "判断深挖或切换", "组织下一轮问题"]
      : ["恢复面试状态", "连接实时通道", "同步最新进度"]

  return (
    <div style={{ display: "grid", placeItems: "center", flex: 1, padding: "2rem", textAlign: "center" }}>
      <div style={{ width: "min(100%, 520px)" }}>
        <div
          className="llm-orbit"
          style={{
            width: 68,
            height: 68,
            margin: "0 auto",
            borderRadius: 22,
            display: "grid",
            placeItems: "center",
            color: "var(--wj-brand-secondary)",
            background: "linear-gradient(145deg, var(--wj-brand-accent-bg), #fff)",
            border: "1px solid rgb(14 165 160 / 20%)",
            boxShadow: "0 16px 36px rgb(13 27 42 / 10%)",
          }}
        >
          {mode === "question" ? <BrainCircuit size={30} /> : <LoaderCircle size={30} style={{ animation: "spin 1.4s linear infinite" }} />}
        </div>
        <h2 style={{ margin: "1rem 0 0", color: "var(--wj-text-primary)", fontSize: "1.15rem", fontWeight: 650 }}>
          {mode === "question" ? "正在准备有价值的下一问" : "正在恢复面试现场"}
        </h2>
        <p style={{ margin: "0.45rem 0 0", color: "var(--wj-text-secondary)", lineHeight: 1.7 }}>{message}</p>
        <div className="llm-progress-track" style={{ marginTop: "1.1rem" }} />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.55rem", marginTop: "0.9rem" }}>
          {steps.map((step, index) => (
            <div key={step} className="app-muted-surface" style={{ padding: "0.65rem 0.45rem", fontSize: "0.76rem", color: "var(--wj-text-secondary)" }}>
              <span style={{ color: "var(--wj-brand-secondary)", fontWeight: 700 }}>{index + 1}</span> · {step}
            </div>
          ))}
        </div>
        <p style={{ margin: "0.85rem 0 0", color: "var(--wj-text-tertiary)", fontSize: "0.78rem" }}>
          已等待 {seconds} 秒 · 可以暂时离开，返回后会自动恢复
        </p>
      </div>
    </div>
  )
}

function AnalysisProgress({
  hasAnalysis,
  hasEvaluation,
  hasEvidence,
  hasCoaching,
  submissionKey,
}: {
  hasAnalysis: boolean
  hasEvaluation: boolean
  hasEvidence: boolean
  hasCoaching: boolean
  submissionKey: string
}) {
  const steps = [
    { label: "理解回答", detail: "提取技术点与个人贡献", icon: FileSearch, done: hasAnalysis },
    { label: "多维评分", detail: "生成六维评价与缺失点", icon: BrainCircuit, done: hasEvaluation },
    { label: "证据核验", detail: "对照简历与前序回答", icon: ShieldCheck, done: hasEvidence },
    { label: "预期回答", detail: "整理强回答示例与追问方向", icon: Sparkles, done: hasCoaching },
  ]

  return (
    <div className="app-muted-surface" style={{ padding: "1.15rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontWeight: 650, color: "var(--wj-text-primary)" }}>问鉴正在分阶段整理本题反馈</div>
          <div style={{ marginTop: "0.3rem", color: "var(--wj-text-secondary)", fontSize: "0.84rem", lineHeight: 1.6 }}>
            评分先返回即可先看；预期回答会在评分结果基础上继续完善。
          </div>
        </div>
        <LoaderCircle size={20} style={{ flexShrink: 0, color: "var(--wj-brand-secondary)", animation: "spin 1.1s linear infinite" }} />
      </div>
      <div className="llm-progress-track" style={{ marginTop: "0.9rem" }} />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: "0.55rem", marginTop: "0.9rem" }}>
        {steps.map(({ label, detail, icon: Icon, done }) => (
          <div key={label} style={{ padding: "0.75rem", borderRadius: 12, background: done ? "var(--wj-success-bg)" : "var(--wj-bg-surface)", border: "1px solid var(--wj-border-default)" }}>
            <Icon size={16} color={done ? "var(--wj-success)" : "var(--wj-brand-secondary)"} />
            <div style={{ marginTop: "0.45rem", color: "var(--wj-text-primary)", fontWeight: 600, fontSize: "0.8rem" }}>{label}</div>
            <div style={{ marginTop: "0.2rem", color: "var(--wj-text-tertiary)", fontSize: "0.72rem", lineHeight: 1.45 }}>{detail}</div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: "0.75rem", color: "var(--wj-text-tertiary)", fontSize: "0.74rem" }}>
        可安全刷新或稍后重进，结果会自动恢复{submissionKey ? ` · 提交 ${submissionKey.slice(-8)}` : ""}
      </div>
    </div>
  )
}

function ScorePill({ evaluation }: { evaluation: Record<string, unknown> }) {
  const dims = (evaluation.dimensions as Array<Record<string, unknown>>) || []
  if (!dims.length) return null

  let weightedScore = 0
  let totalWeight = 0
  for (const dimension of dims) {
    const weight = DIMENSION_WEIGHTS[(dimension.dimension as string) || ""] || 0
    weightedScore += ((dimension.score as number) || 0) * weight
    totalWeight += weight
  }
  const total = totalWeight ? Math.round(weightedScore / totalWeight) : null
  if (total == null) return null

  return (
    <span
      style={{
        padding: "0.18rem 0.5rem",
        borderRadius: 999,
        background: total >= 70 ? "var(--wj-success-bg)" : total >= 50 ? "var(--wj-warning-bg)" : "var(--wj-error-bg)",
        color: total >= 70 ? "var(--wj-success)" : total >= 50 ? "var(--wj-warning)" : "var(--wj-error)",
        fontSize: "0.76rem",
        fontWeight: 700,
      }}
    >
      {total}
    </span>
  )
}

function ScoreDisplay({ evaluation }: { evaluation: Record<string, unknown> }) {
  const dims = (evaluation.dimensions as Array<Record<string, unknown>>) || []
  const strengths = (evaluation.strengths as string[]) || []
  const problems = [
    ...((evaluation.factual_errors as string[]) || []),
    ...((evaluation.key_missing_points as string[]) || []),
    ...((evaluation.unsupported_claims as string[]) || []),
  ].filter((item, index, all) => item && all.indexOf(item) === index)
  const scoringFailed = evaluation.scoring_failed === true

  let weightedScore = 0
  let totalWeight = 0
  for (const dimension of dims) {
    const weight = DIMENSION_WEIGHTS[(dimension.dimension as string) || ""] || 0
    weightedScore += ((dimension.score as number) || 0) * weight
    totalWeight += weight
  }
  const total = totalWeight ? Math.round(weightedScore / totalWeight) : null

  return (
    <div style={{ display: "grid", gap: "0.8rem" }}>
      {scoringFailed ? (
        <div
          style={{
            padding: "0.85rem 0.95rem",
            borderRadius: 12,
            background: "var(--wj-error-bg)",
            border: "1px solid var(--wj-error)",
            color: "var(--wj-error)",
            fontSize: "0.86rem",
            lineHeight: 1.7,
          }}
        >
          本次评分未能生成：模型返回的结果无法解析，评分数据已缺失。你可以在下一轮补充回答，问鉴会继续核验证据并给出分数。
        </div>
      ) : null}
      {total != null ? (
        <div style={{ display: "flex", alignItems: "baseline", gap: "0.35rem" }}>
          <span style={{ fontSize: "2rem", fontWeight: 700, color: "var(--wj-text-primary)" }}>{total}</span>
          <span style={{ color: "var(--wj-text-secondary)" }}>/ 100</span>
        </div>
      ) : null}
      {dims.length ? (
        <div style={{ display: "grid", gap: "0.45rem" }}>
          {dims.map((dimension, index) => (
            <div key={index} style={{ display: "flex", justifyContent: "space-between", gap: "1rem", fontSize: "0.84rem" }}>
              <span style={{ color: "var(--wj-text-secondary)" }}>{dimensionLabel(dimension.dimension as string)}</span>
              <strong style={{ color: "var(--wj-text-primary)" }}>
                {String(dimension.score ?? 0)} / {String(dimension.max_score ?? 100)}
              </strong>
            </div>
          ))}
        </div>
      ) : scoringFailed ? null : (
        <div style={{ color: "var(--wj-text-secondary)", fontSize: "0.84rem" }}>评分数据仍在整理中。</div>
      )}
      {strengths.length ? <TextList title="回答亮点" items={strengths} color="var(--wj-success)" /> : null}
      {problems.length ? <TextList title="需要改进" items={problems} color="var(--wj-error)" /> : null}
    </div>
  )
}

function CoachingDisplay({ coaching }: { coaching: Record<string, unknown> }) {
  const summary = (coaching.score_summary as string) || (coaching.question_analysis as string) || ""
  const good = (coaching.what_was_good as string[]) || []
  const improve = (coaching.what_to_improve as string[]) || []
  const expertAnswer = (coaching.expert_answer as string) || (coaching.complete_answer as string) || ""

  return (
    <div style={{ display: "grid", gap: "0.75rem", color: "var(--wj-text-secondary)", lineHeight: 1.7, fontSize: "0.86rem" }}>
      {summary ? <p style={{ margin: 0 }}>{summary}</p> : null}
      {good.length ? <TextList title="做得较好的地方" items={good} color="var(--wj-success)" /> : null}
      {improve.length ? <TextList title="建议继续补强" items={improve} color="var(--wj-warning)" /> : null}
      {expertAnswer ? (
        <div className="app-muted-surface" style={{ padding: "0.85rem 0.95rem" }}>
          <div style={{ fontWeight: 600, color: "var(--wj-text-primary)", marginBottom: "0.35rem" }}>预期回答（强回答示例）</div>
          <div style={{ marginBottom: "0.55rem", color: "var(--wj-text-tertiary)", fontSize: "0.76rem" }}>
            这是基于题目考察点生成的示例框架，不代表你未陈述的项目事实；请用自己的真实经历补全。
          </div>
          <div style={{ whiteSpace: "pre-wrap" }}>{expertAnswer}</div>
        </div>
      ) : null}
    </div>
  )
}

function TextList({ title, items, color }: { title: string; items: string[]; color: string }) {
  return (
    <div>
      <div style={{ fontWeight: 600, color, marginBottom: "0.35rem" }}>{title}</div>
      <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
        {items.map((item, index) => (
          <li key={index} style={{ marginBottom: "0.25rem" }}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: "0.8rem", marginBottom: "0.45rem", fontSize: "0.82rem" }}>
      <span style={{ color: "var(--wj-text-tertiary)" }}>{label}</span>
      <span style={{ color: "var(--wj-text-primary)", fontWeight: 500, textAlign: "right" }}>{value}</span>
    </div>
  )
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

function formatQuestionForm(form: string): string {
  const formLabels: Record<string, string> = {
    concept: "概念理解",
    project_detail: "项目细节",
    debugging: "调试追踪",
    tradeoff: "权衡决策",
    counterfactual: "反事实",
    clarification: "澄清",
  }
  return formLabels[form] || form
}
