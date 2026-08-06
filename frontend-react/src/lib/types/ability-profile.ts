/**
 * Ability Profile types for Phase 2.4
 */

export type StabilityLevel = "LOW" | "MEDIUM" | "HIGH"
export type TransferStatus = "UNTESTED" | "PARTIAL" | "DEMONSTRATED"
export type ScoreTrend = "IMPROVING" | "STABLE" | "DECLINING" | null

/**
 * Stability factors that feed the stability level calculation.
 */
export interface StabilityFactors {
  session_count: number
  form_diversity: number
  score_consistency: number // 0.0 - 1.0
  evidence_strength: number // 0.0 - 1.0
  stability_score: number // 0.0 - 1.0
}

/**
 * Aggregated metrics for a single competency across interviews.
 */
export interface CompetencyProfile {
  total_interviews: number
  total_questions: number
  forms_used: string[]
  avg_score: number
  score_trend: ScoreTrend
  stability: StabilityLevel
  stability_factors: StabilityFactors
  transfer_status: TransferStatus
  counterfactual_performance: number | null
  last_evidence_status: string
  last_verification_date: string | null
  unresolved_gaps: string[]
}

/**
 * A single competency's profile plus per-interview score history.
 */
export interface CompetencySummary {
  competency_code: string
  profile: CompetencyProfile
  history: Array<{
    interview_id: string
    score: number
    created_at: string | null
  }>
}

/**
 * Ability profile result for a resume.
 */
export interface AbilityProfileResult {
  resume_id: string
  total_interviews: number
  competencies: CompetencySummary[]
}
