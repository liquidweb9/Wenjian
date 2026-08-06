/**
 * Answer diff types for Phase 2.4 — same-question re-answer comparison.
 */

/** Diff summary between two consecutive answer versions. */
export interface AnswerDiffSummary {
  added_tokens: string[]
  removed_tokens: string[]
  total_added: number
  total_removed: number
  total_common: number
  change_ratio: number
  new_evidence: boolean
  coaching_repetition: boolean
  is_substantive_change: boolean
  original_hash: string
  revised_hash: string
}

/** A single answer version for a question. */
export interface AnswerVersion {
  version_number: number
  answer_id: string
  answer_text: string
  created_at: string | null
  score: number | null
  /** Present on version 2+; null on the first version. */
  diff: AnswerDiffSummary | null
}

/** Result of fetching answer versions for a question. */
export interface AnswerVersionResult {
  interview_id: string
  question_id: string
  versions: AnswerVersion[]
}
