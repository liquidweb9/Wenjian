import { useQuery } from "@tanstack/react-query"
import { queryKeys } from "@/lib/query-keys"
import { abilityProfileApi } from "../api/ability-profile-api"

export function useAbilityProfile(resumeId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.abilities.profile(resumeId ?? ""),
    queryFn: () => abilityProfileApi.getProfile(resumeId!),
    enabled: !!resumeId,
  })
}
