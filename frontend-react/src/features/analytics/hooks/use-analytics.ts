import { useQuery } from "@tanstack/react-query"
import { queryKeys } from "@/lib/query-keys"
import { getAnalyticsSummary, getAnalyticsTrends } from "../api/analytics-api"

export function useAnalyticsSummary() {
  return useQuery({
    queryKey: queryKeys.analytics.summary,
    queryFn: getAnalyticsSummary,
    staleTime: 60_000,
  })
}

export function useAnalyticsTrends() {
  return useQuery({
    queryKey: queryKeys.analytics.trends,
    queryFn: getAnalyticsTrends,
    staleTime: 60_000,
  })
}
