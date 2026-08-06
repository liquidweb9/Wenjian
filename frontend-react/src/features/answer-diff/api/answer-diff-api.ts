import { api } from "@/lib/api-client"
import type { AnswerVersionResult } from "@/lib/types/answer-diff"

export const answerDiffApi = {
  async getVersions(interviewId: string, questionId: string): Promise<AnswerVersionResult> {
    const response = await api.get<AnswerVersionResult>(
      `/interviews/${interviewId}/questions/${questionId}/versions`,
    )
    return response.data
  },
}
