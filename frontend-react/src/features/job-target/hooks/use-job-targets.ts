import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { jobTargetApi } from "@/features/job-target/api/job-target-api"
import type {
  JobTargetCreateRequest,
  ParseJDRequest,
  RequirementUpdateRequest,
} from "@/lib/types/job-target"

/**
 * Query keys for job targets
 */
export const jobTargetKeys = {
  all: ["job-targets"] as const,
  lists: () => [...jobTargetKeys.all, "list"] as const,
  list: (filters?: Record<string, unknown>) => [...jobTargetKeys.lists(), filters] as const,
  details: () => [...jobTargetKeys.all, "detail"] as const,
  detail: (id: string) => [...jobTargetKeys.details(), id] as const,
  templates: () => [...jobTargetKeys.all, "templates"] as const,
}

/**
 * Fetch all job targets
 */
export function useJobTargets() {
  return useQuery({
    queryKey: jobTargetKeys.list(),
    queryFn: () => jobTargetApi.list(),
  })
}

/**
 * Fetch a single job target
 */
export function useJobTarget(jobTargetId: string | undefined) {
  return useQuery({
    queryKey: jobTargetKeys.detail(jobTargetId!),
    queryFn: () => jobTargetApi.get(jobTargetId!),
    enabled: !!jobTargetId,
  })
}

/**
 * Get job target templates (local, no API call)
 */
export function useJobTargetTemplates() {
  return useQuery({
    queryKey: jobTargetKeys.templates(),
    queryFn: () => jobTargetApi.getTemplates(),
    staleTime: Infinity, // Templates never change
  })
}

/**
 * Create a new job target
 */
export function useCreateJobTarget() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: JobTargetCreateRequest) => jobTargetApi.create(data),
    onSuccess: () => {
      // Invalidate list to refetch
      queryClient.invalidateQueries({ queryKey: jobTargetKeys.lists() })
    },
  })
}

/**
 * Update a job target
 */
export function useUpdateJobTarget() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ jobTargetId, data }: { jobTargetId: string; data: Partial<JobTargetCreateRequest> }) =>
      jobTargetApi.update(jobTargetId, data),
    onSuccess: (_, variables) => {
      // Invalidate both list and detail
      queryClient.invalidateQueries({ queryKey: jobTargetKeys.lists() })
      queryClient.invalidateQueries({ queryKey: jobTargetKeys.detail(variables.jobTargetId) })
    },
  })
}

/**
 * Delete a job target
 */
export function useDeleteJobTarget() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (jobTargetId: string) => jobTargetApi.delete(jobTargetId),
    onSuccess: () => {
      // Invalidate list to refetch
      queryClient.invalidateQueries({ queryKey: jobTargetKeys.lists() })
    },
  })
}

/**
 * Parse JD text into structured requirements
 */
export function useParseJD() {
  return useMutation({
    mutationFn: (data: ParseJDRequest) => jobTargetApi.parseJD(data),
  })
}

/**
 * Update a specific requirement
 */
export function useUpdateRequirement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      jobTargetId,
      requirementId,
      data,
    }: {
      jobTargetId: string
      requirementId: string
      data: RequirementUpdateRequest
    }) => jobTargetApi.updateRequirement(jobTargetId, requirementId, data),
    onSuccess: (_, variables) => {
      // Invalidate detail to refetch
      queryClient.invalidateQueries({ queryKey: jobTargetKeys.detail(variables.jobTargetId) })
    },
  })
}
