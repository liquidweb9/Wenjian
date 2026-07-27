import { useEffect, useReducer, useRef } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { queryKeys } from "@/lib/query-keys"
import { eventReducer, initialState } from "../runtime/event-reducer"
import { createSSEConnection } from "../api/interview-sse"
import type { InterviewRuntimeState } from "../runtime/event-schema"

export function useInterviewStream(
  interviewId: string | undefined,
  persistedQuestion?: Record<string, unknown> | null,
): InterviewRuntimeState {
  const [state, dispatch] = useReducer(eventReducer, initialState)
  const qc = useQueryClient()
  const cleanupRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    if (!interviewId) return

    const controller = new AbortController()

    cleanupRef.current = createSSEConnection(
      interviewId,
      (event) => {
        dispatch(event)
        const eventType = event.event_type as string
        if (
          eventType === "question.ready" ||
          eventType === "interview.finished" ||
          eventType === "report.ready"
        ) {
          qc.invalidateQueries({ queryKey: queryKeys.interviews.detail(interviewId) })
        }
      },
      (connState) => {
        dispatch({ event_type: "_connection_change", payload: { state: connState }, sequence: 0 })
      },
      controller.signal,
    )

    return () => {
      cleanupRef.current?.()
      controller.abort()
    }
  }, [interviewId, qc])

  useEffect(() => {
    if (persistedQuestion?.question_id) {
      dispatch({
        event_type: "question.ready",
        payload: persistedQuestion,
        sequence: 0,
      })
    }
  }, [persistedQuestion])

  return state
}
