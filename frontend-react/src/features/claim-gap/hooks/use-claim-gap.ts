import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { claimGapApi } from "@/features/claim-gap/api/claim-gap-api"
import type { GapAnalysisRequest } from "@/lib/types/claim-gap"

/**
 * Query keys for claim gap
 */
export const claimGapKeys = {
  all: ["claim-gap"] as const,
  analyses: () => [...claimGapKeys.all, "analysis"] as const,
  analysis: (resumeId: string, jobTargetId: string) =>
    [...claimGapKeys.analyses(), resumeId, jobTargetId] as const,
}

/**
 * Get cached gap analysis
 */
export function useGapAnalysis(resumeId: string | undefined, jobTargetId: string | undefined) {
  return useQuery({
    queryKey: claimGapKeys.analysis(resumeId!, jobTargetId!),
    queryFn: () => claimGapApi.getGapAnalysis(resumeId!, jobTargetId!),
    enabled: !!resumeId && !!jobTargetId,
  })
}

/**
 * Alias for backward compatibility
 */
export function useClaimGap(resumeId: string | undefined, jobTargetId: string | undefined) {
  return useGapAnalysis(resumeId, jobTargetId)
}

/**
 * Analyze gap (trigger new analysis)
 */
export function useAnalyzeGap() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: GapAnalysisRequest) => claimGapApi.analyzeGap(request),
    onSuccess: (data) => {
      // Cache the result
      queryClient.setQueryData(
        claimGapKeys.analysis(data.resume_id, data.job_target_id),
        data
      )
    },
  })
}
