import { api } from "@/lib/api-client"

export interface AnalyticsSummary {
  total_interviews: number
  average_score: number | null
  score_distribution: Record<string, number>
  top_abilities: Array<{ name: string; score: number }>
  weak_abilities: Array<{ name: string; score: number }>
  claim_verification_rate: number | null
  claim_status_counts: Record<string, number>
}

export interface AnalyticsTrends {
  interviews_over_time: Array<{ week: string; count: number }>
  score_trend: Array<{ date: string; score: number }>
}

export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const { data } = await api.get<AnalyticsSummary>("/analytics/summary")
  return data
}

export async function getAnalyticsTrends(): Promise<AnalyticsTrends> {
  const { data } = await api.get<AnalyticsTrends>("/analytics/trends")
  return data
}
