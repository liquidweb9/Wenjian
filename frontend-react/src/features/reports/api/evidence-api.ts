import { api } from "@/lib/api-client"

// ============================================================
// Types
// ============================================================

export interface EvidenceSpan {
  start: number
  end: number
  text: string
  quote_hash: string
}

export interface VerificationPoint {
  verification_point_id: string
  claim_id: string
  competency_code: string
  aspect: string
  current_state: string
  strength: number | null
  confidence: string | null
  evidence_count: number
  transition_count: number
  has_contradictions: boolean
  created_at: string
  updated_at: string
}

export interface EvidenceTransition {
  transition_id: string
  verification_point_id: string
  from_state: string
  to_state: string
  reason_code: string
  answer_id: string | null
  evidence_spans: EvidenceSpan[] | null
  policy_version: string
  created_at: string
}

export interface Contradiction {
  contradiction_id: string
  verification_point_id: string
  claim_id: string
  contradiction_type: string
  severity: string
  description: string
  clarification_question: string | null
  conflicting_answers: Array<{ answer_id: string; text: string }>
  resolution_status: string
  created_at: string
}

export interface Evidence {
  evidence_id: string
  answer_id: string
  evidence_type: string
  spans: EvidenceSpan[]
  summary: string
  extracted_by: string
  confidence: number
  created_at: string
}

// ============================================================
// API Response Types
// ============================================================

export interface VerificationPointsResponse {
  verification_points: VerificationPoint[]
}

export interface TransitionsResponse {
  verification_point_id: string
  current_state: string
  transitions: EvidenceTransition[]
}

export interface ContradictionsResponse {
  interview_id: string
  total_count: number
  contradictions: Contradiction[]
}

export interface EvidenceResponse {
  verification_point_id: string
  aspect: string
  current_state: string
  evidence_count: number
  evidence: Evidence[]
}

// ============================================================
// API Functions
// ============================================================

export async function getVerificationPointsForClaim(
  claimId: string,
): Promise<VerificationPointsResponse> {
  const { data } = await api.get<VerificationPointsResponse>(
    `/evidence/verification-points/${claimId}`,
  )
  return data
}

export async function getTransitionsForVerificationPoint(
  verificationPointId: string,
): Promise<TransitionsResponse> {
  const { data } = await api.get<TransitionsResponse>(
    `/evidence/transitions/${verificationPointId}`,
  )
  return data
}

export async function getContradictionsForInterview(
  interviewId: string,
  resolutionStatus?: string,
): Promise<ContradictionsResponse> {
  const params = resolutionStatus ? { resolution_status: resolutionStatus } : undefined
  const { data } = await api.get<ContradictionsResponse>(
    `/evidence/contradictions/${interviewId}`,
    { params },
  )
  return data
}

export async function getEvidenceForVerificationPoint(
  verificationPointId: string,
): Promise<EvidenceResponse> {
  const { data } = await api.get<EvidenceResponse>(
    `/evidence/evidence/${verificationPointId}`,
  )
  return data
}
