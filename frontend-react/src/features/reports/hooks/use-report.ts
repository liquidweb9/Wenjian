import { useQuery } from "@tanstack/react-query"
import { queryKeys } from "@/lib/query-keys"
import { getReport } from "../api/report-api"

export function useReport(interviewId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.interviews.report(interviewId ?? ""),
    queryFn: () => getReport(interviewId!),
    enabled: !!interviewId,
  })
}
