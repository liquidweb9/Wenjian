import { api } from "@/lib/api-client"
import type { AbilityProfileResult } from "@/lib/types/ability-profile"

export const abilityProfileApi = {
  async getProfile(resumeId: string): Promise<AbilityProfileResult> {
    const response = await api.get<AbilityProfileResult>(`/abilities/profile/${resumeId}`)
    return response.data
  },
}
