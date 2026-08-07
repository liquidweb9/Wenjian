import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { queryKeys } from "@/lib/query-keys"
import * as resumeApi from "../api/resume-api"
import type { ResumeListParams } from "../api/resume-api"

export function useResumeList(filters: ResumeListParams = {}) {
  return useQuery({
    queryKey: queryKeys.resumes.list(filters),
    queryFn: () => resumeApi.listResumes(filters),
  })
}

export function useResume(resumeId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.resumes.detail(resumeId ?? ""),
    queryFn: () => resumeApi.getResume(resumeId!),
    enabled: !!resumeId,
  })
}

export function useResumeClaims(resumeId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.resumes.claims(resumeId ?? ""),
    queryFn: () => resumeApi.getClaims(resumeId!),
    enabled: !!resumeId,
  })
}

export function useResumeRevisions(resumeId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.resumes.revisions(resumeId ?? ""),
    queryFn: () => resumeApi.getRevisions(resumeId!),
    enabled: !!resumeId,
  })
}

export function useUploadResumeFile() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: resumeApi.uploadResumeFile,
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: queryKeys.resumes.all })
      navigate(`/app/resumes/${data.resume_id}/review`)
    },
  })
}

export function useUploadResumeText() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: ({ fileName, text }: { fileName: string; text: string }) =>
      resumeApi.uploadResumeText(fileName, text),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: queryKeys.resumes.all })
      navigate(`/app/resumes/${data.resume_id}/review`)
    },
  })
}

export function useUpdateRevision() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      resumeId,
      revisionId,
      text,
    }: { resumeId: string; revisionId: string; text: string }) =>
      resumeApi.updateRevision(resumeId, revisionId, text),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.resumes.detail(vars.resumeId) })
    },
  })
}

export function useConfirmRevision() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      resumeId,
      revisionId,
      targetRole,
      jobTargetId,
    }: {
      resumeId: string
      revisionId: string
      targetRole: string
      jobTargetId?: string | null
    }) => resumeApi.confirmRevision(resumeId, revisionId, targetRole, jobTargetId),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.resumes.detail(vars.resumeId) })
      qc.invalidateQueries({ queryKey: queryKeys.resumes.claims(vars.resumeId) })
      qc.invalidateQueries({ queryKey: queryKeys.resumes.all })
    },
  })
}

export function useUpdateTargetRole() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      resumeId,
      targetRole,
      jobTargetId,
    }: {
      resumeId: string
      targetRole: string
      jobTargetId?: string | null
    }) => resumeApi.updateResumeTargetRole(resumeId, { target_role: targetRole, job_target_id: jobTargetId }),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.resumes.detail(vars.resumeId) })
      qc.invalidateQueries({ queryKey: queryKeys.resumes.claims(vars.resumeId) })
    },
  })
}

export function useUpdateClaim() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      resumeId,
      claimId,
      updates,
    }: { resumeId: string; claimId: string; updates: { enabled?: boolean; priority?: number } }) =>
      resumeApi.updateClaim(resumeId, claimId, updates),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.resumes.claims(vars.resumeId) })
    },
  })
}

export function useDeleteResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: resumeApi.deleteResume,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.resumes.all })
    },
  })
}
