import type { ConnectionState, InterviewRuntimeState } from "./event-schema"

export function eventReducer(
  state: InterviewRuntimeState,
  event: Record<string, unknown>,
): InterviewRuntimeState {
  const eventType = (event.event_type as string) || ""
  const payload = (event.payload || {}) as Record<string, unknown>
  const seq = (event.sequence as number) || 0

  // Internal events bypass sequence dedup
  if (eventType !== "_connection_change" && seq <= state.lastSequence && state.lastSequence > 0) {
    return state
  }

  const next: InterviewRuntimeState = { ...state, lastSequence: seq }

  switch (eventType) {
    case "_connection_change":
      return { ...state, connection: (payload.state as ConnectionState) || "idle" }

    case "interview.initialized":
      return { ...next, currentStage: "waiting_for_question" }

    case "question.ready":
      return {
        ...next,
        currentStage: "answering",
        latestEvaluation: null,
        latestCoaching: null,
        currentQuestion: {
          question_id: payload.question_id,
          question_text: payload.question_text,
          ...payload,
        },
      }

    case "answer.accepted":
      return { ...next, currentStage: "analyzing" }

    case "analysis.completed":
      return { ...next, currentStage: "analyzing" }

    case "scoring.completed":
      return {
        ...next,
        currentStage: "analyzing",
        latestEvaluation: (payload.evaluation as Record<string, unknown>) || null,
      }

    case "coaching.ready":
      return {
        ...next,
        latestCoaching: (payload.coaching as Record<string, unknown>) || null,
      }

    case "interview.finished":
      return { ...next, currentStage: "finished" }

    case "report.ready":
      return { ...next, currentStage: "finished" }

    default:
      return next
  }
}

export const initialState: InterviewRuntimeState = {
  connection: "idle",
  lastSequence: 0,
  currentStage: "loading",
  currentQuestion: null,
  latestEvaluation: null,
  latestCoaching: null,
  lastError: null,
}
