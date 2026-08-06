import { useQuery } from "@tanstack/react-query"
import { queryKeys } from "@/lib/query-keys"
import { answerDiffApi } from "../api/answer-diff-api"

export function useAnswerVersions(interviewId: string | undefined, questionId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.answerDiff.versions(interviewId ?? "", questionId ?? ""),
    queryFn: () => answerDiffApi.getVersions(interviewId!, questionId!),
    enabled: !!interviewId && !!questionId,
  })
}
