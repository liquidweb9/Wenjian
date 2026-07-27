import { api } from "@/lib/api-client"

export interface DashboardSummary {
  total_resumes: number
  total_interviews: number
  pending_reviews: number
  completed_interviews: number
  in_progress_count: number
  average_score: number | null
  recent_resumes: Array<{
    resume_id: string
    file_name: string
    source_type: string
    created_at: string | null
    status: string | null
  }>
  in_progress_interviews: Array<{
    interview_id: string
    resume_id: string
    target_role: string
    mode: string
    status: string
    max_turns: number
    created_at: string | null
  }>
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await api.get<DashboardSummary>("/dashboard/summary")
  return data
}
