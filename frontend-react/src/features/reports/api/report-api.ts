import { api } from "@/lib/api-client"

export interface ReportData {
  interview_id: string
  report: Record<string, unknown> | null
  created_at?: string | null
}

export async function getReport(interviewId: string): Promise<ReportData> {
  const { data } = await api.get<ReportData>(`/interviews/${interviewId}/report`)
  return data
}

export async function exportReport(
  interviewId: string,
  format: "json" | "markdown" = "json",
): Promise<unknown> {
  const { data } = await api.post(`/interviews/${interviewId}/report/export`, { format })
  return data
}
