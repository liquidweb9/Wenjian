import { useQuery } from "@tanstack/react-query"
import { queryKeys } from "@/lib/query-keys"
import {
  getVerificationPointsForClaim,
  getTransitionsForVerificationPoint,
  getContradictionsForInterview,
  getEvidenceForVerificationPoint,
} from "../api/evidence-api"

export function useVerificationPoints(claimId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.evidence.verificationPoints(claimId ?? ""),
    queryFn: () => getVerificationPointsForClaim(claimId!),
    enabled: !!claimId,
  })
}

export function useTransitions(verificationPointId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.evidence.transitions(verificationPointId ?? ""),
    queryFn: () => getTransitionsForVerificationPoint(verificationPointId!),
    enabled: !!verificationPointId,
  })
}

export function useContradictions(interviewId: string | undefined, resolutionStatus?: string) {
  return useQuery({
    queryKey: queryKeys.evidence.contradictions(interviewId ?? "", resolutionStatus),
    queryFn: () => getContradictionsForInterview(interviewId!, resolutionStatus),
    enabled: !!interviewId,
  })
}

export function useEvidence(verificationPointId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.evidence.evidence(verificationPointId ?? ""),
    queryFn: () => getEvidenceForVerificationPoint(verificationPointId!),
    enabled: !!verificationPointId,
  })
}
