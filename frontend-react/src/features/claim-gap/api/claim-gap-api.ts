import { api } from "@/lib/api-client"
import type { GapAnalysisResult, GapAnalysisRequest } from "@/lib/types/claim-gap"

/**
 * Claim Gap API layer
 */
export const claimGapApi = {
  /**
   * Analyze gap between resume claims and job target requirements
   */
  async analyzeGap(request: GapAnalysisRequest): Promise<GapAnalysisResult> {
    const response = await api.post<GapAnalysisResult>("/claim-gap", request)
    return response.data
  },

  /**
   * Get cached gap analysis if available
   */
  async getGapAnalysis(resumeId: string, jobTargetId: string): Promise<GapAnalysisResult> {
    const response = await api.get<GapAnalysisResult>(
      `/claim-gap/resume/${resumeId}/job-target/${jobTargetId}`
    )
    return response.data
  },
}
