import { api } from "@/lib/api-client"

export interface ResumeListParams {
  page?: number
  page_size?: number
  search?: string
  status?: string
  sort_by?: string
  sort_order?: string
}

export interface ResumeSummary {
  resume_id: string
  file_name: string
  source_type: string
  status: string | null
  created_at: string | null
  latest_revision_id: string | null
}

export interface ResumeDetail {
  resume_id: string
  file_name: string
  source_type: string
  status: string | null
  revision_id: string | null
  latest_revision_id: string | null
  normalized_text: string | null
  raw_text: string | null
  extraction_quality: number | null
  extraction_warnings: string[]
  extraction_method: string | null
  parser_name: string | null
  parser_version: string | null
  profile: Record<string, unknown> | null
  created_at: string | null
}

export interface ClaimItem {
  claim_id: string
  priority: number
  confidence: number
  disabled: boolean
  data: Record<string, unknown>
  created_at: string | null
}

export interface RevisionItem {
  revision_id: string
  status: string
  extraction_quality: number | null
  created_at: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export async function listResumes(params: ResumeListParams = {}) {
  const { data } = await api.get<PaginatedResponse<ResumeSummary>>("/resumes", { params })
  return data
}

export async function getResume(resumeId: string) {
  const { data } = await api.get<ResumeDetail>(`/resumes/${resumeId}`)
  return data
}

export async function getClaims(resumeId: string) {
  const { data } = await api.get<{ resume_id: string; claims: ClaimItem[] }>(
    `/resumes/${resumeId}/claims`,
  )
  return data
}

export async function getRevisions(resumeId: string) {
  const { data } = await api.get<{ resume_id: string; revisions: RevisionItem[] }>(
    `/resumes/${resumeId}/revisions`,
  )
  return data
}

export async function uploadResumeFile(file: File) {
  const form = new FormData()
  form.append("file", file)
  const { data } = await api.post("/resumes", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 180_000,
    onUploadProgress: undefined, // hook callers can monitor via their own approach
  })
  return data
}

export async function uploadResumeText(fileName: string, text: string) {
  const { data } = await api.post("/resumes/text", { file_name: fileName, text })
  return data
}

export async function updateRevision(resumeId: string, revisionId: string, normalizedText: string) {
  const { data } = await api.patch(`/resumes/${resumeId}/revisions/${revisionId}`, {
    normalized_text: normalizedText,
  })
  return data
}

export async function confirmRevision(resumeId: string, revisionId: string, targetRole: string) {
  const { data } = await api.post(
    `/resumes/${resumeId}/revisions/${revisionId}/confirm`,
    null,
    { params: { target_role: targetRole }, timeout: 300_000 },
  )
  return data
}

export async function updateClaim(
  resumeId: string,
  claimId: string,
  updates: { enabled?: boolean; priority?: number },
) {
  const { data } = await api.patch(`/resumes/${resumeId}/claims/${claimId}`, updates)
  return data
}

export async function deleteResume(resumeId: string) {
  const { data } = await api.delete(`/resumes/${resumeId}`)
  return data
}
