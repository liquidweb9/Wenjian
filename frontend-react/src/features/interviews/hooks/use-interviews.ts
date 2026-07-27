import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { queryKeys } from "@/lib/query-keys"
import * as api from "../api/interview-api"
import type { InterviewListParams } from "../api/interview-api"

export function useInterviewList(filters: InterviewListParams = {}) {
  return useQuery({
    queryKey: queryKeys.interviews.list(filters),
    queryFn: () => api.listInterviews(filters),
  })
}

export function useInterview(interviewId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.interviews.detail(interviewId ?? ""),
    queryFn: () => api.getInterview(interviewId!),
    enabled: !!interviewId,
    staleTime: 5_000,
    // SSE is the fast path. Polling is the recovery path after refresh, tab
    // suspension, or a missed event while a long-running LLM chain completes.
    refetchInterval: (query) => {
      const data = query.state.data
      return data && !data.finished ? 5_000 : false
    },
    refetchIntervalInBackground: true,
  })
}

export function useCreateInterview() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: api.createInterview,
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: queryKeys.interviews.all })
      navigate(`/app/interviews/${data.interview_id}/live`)
    },
  })
}

export function useSubmitAnswer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      interviewId,
      questionId,
      answerText,
      idempotencyKey,
    }: {
      interviewId: string
      questionId: string
      answerText: string
      idempotencyKey?: string
    }) => api.submitAnswer(interviewId, questionId, answerText, idempotencyKey),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.interviews.detail(vars.interviewId) })
    },
  })
}

export function useFinishInterview() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.finishInterview,
    onSuccess: (_data, interviewId) => {
      qc.invalidateQueries({ queryKey: queryKeys.interviews.detail(interviewId) })
      qc.invalidateQueries({ queryKey: queryKeys.interviews.all })
    },
  })
}
