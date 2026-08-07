import { api, getAuthToken } from "@/lib/api-client"
import { env } from "@/lib/env"

const SSE_BASE_URL = `${env.VITE_API_BASE_URL.replace(/\/$/, "")}/api/v1`

export interface InterviewListParams {
  page?: number
  page_size?: number
  status?: string
  mode?: string
  resume_id?: string
  search?: string
}

export interface InterviewSummary {
  interview_id: string
  thread_id: string
  resume_id?: string
  target_role?: string
  mode?: string
  status: string
  turn_count: number
  max_turns: number
  finished: boolean
  created_at: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface CreateInterviewParams {
  resume_id: string
  resume_revision_id: string
  target_role: string
  job_description?: string
  job_target_id?: string
  mode?: string
  max_turns?: number
  model_tier?: "auto" | "fast" | "balanced" | "judge"
}

export interface HistoryEntry {
  question_id: string
  question_text: string
  answer_text: string | null
    evaluation: Record<string, unknown> | null
    analysis: Record<string, unknown> | null
    coaching: Record<string, unknown> | null
  }

export interface InterviewDetail {
  interview_id: string
  thread_id: string
  resume_id?: string
  job_target_id?: string
  target_role?: string
  mode?: string
  status: string
  turn_count: number
  max_turns: number
  current_question: {
    question_id: string
    question_text: string
    [key: string]: unknown
  } | null
  finished: boolean
  stop_reason: string | null
  history: HistoryEntry[]
}

export interface SubmitAnswerResponse {
  interview_id: string
  status: string
  turn_count: number
  current_question: Record<string, unknown> | null
  next_question: string | null
  next_question_id: string | null
  analysis: Record<string, unknown> | null
  evaluation: Record<string, unknown> | null
  coaching: Record<string, unknown> | null
  finished: boolean
}

export async function listInterviews(params: InterviewListParams = {}) {
  const { data } = await api.get<PaginatedResponse<InterviewSummary>>("/interviews", { params })
  return data
}

export async function createInterview(params: CreateInterviewParams) {
  const { data } = await api.post("/interviews", {
    resume_id: params.resume_id,
    resume_revision_id: params.resume_revision_id,
    target_role: params.target_role,
    job_description: params.job_description || null,
    job_target_id: params.job_target_id || null,
    mode: params.mode || "simulation",
    max_turns: params.max_turns ?? 15,
    model_tier: params.model_tier || "auto",
  }, {
    // Build plan + generate the first question are LLM calls that routinely
    // exceed the global 120s timeout even though the server completes normally.
    timeout: 600_000,
  })
  return data
}

export async function getInterview(interviewId: string) {
  const { data } = await api.get<InterviewDetail>(`/interviews/${interviewId}`)
  return data
}

export async function submitAnswer(
  interviewId: string,
  questionId: string,
  answerText: string,
  idempotencyKey?: string,
): Promise<SubmitAnswerResponse> {
  const { data } = await api.post(`/interviews/${interviewId}/answers`, {
    question_id: questionId,
    answer_text: answerText,
    idempotency_key: idempotencyKey,
  }, {
    // analyze -> score -> evidence -> coaching -> decision -> next question can
    // exceed the global 120s timeout even when the server completes normally.
    timeout: 600_000,
  })
  return data
}

export async function finishInterview(interviewId: string) {
  const { data } = await api.post(
    `/interviews/${interviewId}/finish`,
    undefined,
    {
      // generate_report aggregates evidence, ability observations, and training
      // plan — LLM-heavy, routinely exceeds the global 120s timeout even when
      // the server completes normally.
      timeout: 600_000,
    },
  )
  return data
}

export async function getInterviewEvents(
  interviewId: string,
  onEvent: (event: Record<string, unknown>) => void,
  signal: AbortSignal,
) {
  const headers: Record<string, string> = { Accept: "text/event-stream" }
  const token = getAuthToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(`${SSE_BASE_URL}/interviews/${interviewId}/events`, {
    headers,
    signal,
  })

  if (!response.ok || !response.body) {
    throw new Error(`SSE connection failed: ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  async function readStream() {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split("\n")
      buffer = lines.pop() || ""

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const event = JSON.parse(line.slice(6))
            onEvent(event)
          } catch {
            // Ignore parse errors for heartbeats / comments
          }
        }
      }
    }
  }

  readStream().catch(() => {})
}
