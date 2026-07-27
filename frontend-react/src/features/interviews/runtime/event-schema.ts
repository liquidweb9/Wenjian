import { z } from "zod"

export const eventEnvelopeSchema = z.object({
  event_id: z.string(),
  event_type: z.string(),
  interview_id: z.string(),
  thread_id: z.string(),
  sequence: z.number().int().nonnegative(),
  created_at: z.string(),
  payload: z.unknown(),
})

export type EventEnvelope = z.infer<typeof eventEnvelopeSchema>

export type ConnectionState = "idle" | "connecting" | "connected" | "reconnecting" | "disconnected" | "failed"

export type InterviewStage =
  | "loading"
  | "connecting"
  | "waiting_for_question"
  | "answering"
  | "submitting"
  | "analyzing"
  | "question_ready"
  | "finishing"
  | "finished"
  | "error"

export interface InterviewRuntimeState {
  connection: ConnectionState
  lastSequence: number
  currentStage: InterviewStage
  currentQuestion: Record<string, unknown> | null
  latestEvaluation: Record<string, unknown> | null
  latestCoaching: Record<string, unknown> | null
  lastError: string | null
}
