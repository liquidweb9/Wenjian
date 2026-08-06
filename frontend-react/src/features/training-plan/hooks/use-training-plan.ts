import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { queryKeys } from "@/lib/query-keys"
import type { TrainingTaskStatus } from "@/lib/types/training-plan"
import { trainingPlanApi } from "../api/training-plan-api"

export function useTrainingPlan(resumeId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.trainingPlan.list(resumeId),
    queryFn: () => trainingPlanApi.list(resumeId),
    enabled: !!resumeId,
  })
}

export function useGenerateTrainingPlan(resumeId: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => trainingPlanApi.generate(resumeId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingPlan.list(resumeId) })
    },
  })
}

export function useUpdateTrainingTask(resumeId: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: TrainingTaskStatus }) =>
      trainingPlanApi.updateStatus(taskId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingPlan.list(resumeId) })
    },
  })
}
