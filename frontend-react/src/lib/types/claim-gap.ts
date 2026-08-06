/**
 * Claim Gap types for Phase 2 — aligned with backend app/api/v1/claim_gap.py
 */

/**
 * Gap classification types (aligned with backend app/planning/claim_gap_analyzer.py GapType)
 */
export type GapType =
  | "SUPPORTED_CLAIM" // Claim is well-supported by evidence
  | "WEAK_EVIDENCE_CLAIM" // Claim exists but evidence is insufficient
  | "HIGH_PRIORITY_WEAK_EVIDENCE" // High-importance requirement with weak evidence
  | "UNCOVERED_REQUIREMENT" // Job requirement not mentioned in resume
  | "IRRELEVANT_CLAIM" // Claim doesn't relate to any job requirement

/**
 * A single gap item returned by the backend
 */
export interface ClaimGap {
  gap_type: GapType
  claim_id: string | null
  requirement_id: string | null
  competency_code: string
  priority: number // 0.0 - 1.0
  reason_codes: string[] // Why this gap exists
  explanation: string
  claim_text: string | null
  requirement_title: string | null
  requirement_importance: number | null // 0.0 - 1.0
  requirement_expected_level: number | null // 1 - 5
  claim_coverage_level: number | null // 0 - 5
}

/**
 * Coverage statistics returned by the backend
 */
export interface CoverageStats {
  total_requirements: number
  covered_requirements: number
  uncovered_requirements: number
  weak_evidence_count: number
  high_priority_gaps: number
  coverage_percentage: number // 0.0 - 1.0
}

/**
 * Interview plan target
 */
export interface InterviewTarget {
  claim_id: string | null
  requirement_id: string | null
  competency_code: string
  priority: number
  reason_codes: string[]
  explanation: string
  gap_type: string
  claim_text: string | null
  requirement_title: string | null
}

/**
 * Interview plan returned by the backend
 */
export interface InterviewPlan {
  total_targets: number
  high_priority_count: number
  targets: InterviewTarget[]
}

/**
 * Gap analysis result (backend ClaimGapResponse)
 */
export interface GapAnalysisResult {
  resume_id: string
  job_target_id: string
  gaps: ClaimGap[]
  coverage_stats: CoverageStats
  interview_plan: InterviewPlan
  high_priority_targets: string[]
}

/**
 * Gap analysis request
 */
export interface GapAnalysisRequest {
  resume_id: string
  job_target_id: string
}
