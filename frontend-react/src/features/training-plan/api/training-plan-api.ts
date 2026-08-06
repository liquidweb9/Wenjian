import { api } from "@/lib/api-client"
import type { TrainingTaskResult, TrainingTaskStatus } from "@/lib/types/training-plan"

export const trainingPlanApi = {
  async list(resumeId?: string): Promise<TrainingTaskResult> {
    const params = resumeId ? { resume_id: resumeId } : undefined
    const response = await api.get<TrainingTaskResult>("/training-plans", { params })
    return response.data
  },

  async generate(resumeId: string): Promise<TrainingTaskResult> {
    const response = await api.post<TrainingTaskResult>(`/training-plans/${resumeId}/generate`)
    return response.data
  },

  async updateStatus(taskId: string, status: TrainingTaskStatus): Promise<void> {
    await api.patch(`/training-plans/${taskId}`, { status })
  },
}
