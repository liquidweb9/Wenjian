/**
 * Job Target and Requirement types for Phase 2
 */

// Job level options
export type JobLevel = "intern" | "junior" | "mid" | "senior" | "staff"

// Interview round options
export type InterviewRound = "resume" | "project" | "technical" | "system_design"

// Job target source
export type JobTargetSource = "template" | "pasted_jd" | "manual"

/**
 * Competency code (backend + AI agent engineering)
 */
export type CompetencyCode =
  // Backend competencies
  | "backend.language_runtime"
  | "backend.api_protocol"
  | "backend.database_modeling"
  | "backend.transaction_consistency"
  | "backend.cache"
  | "backend.message_queue"
  | "backend.concurrency"
  | "backend.observability"
  | "backend.failure_recovery"
  | "backend.security"
  | "backend.system_design"
  | "backend.testing"
  | "backend.delivery"
  // AI Agent competencies
  | "agent.prompt_design"
  | "agent.structured_output"
  | "agent.workflow_orchestration"
  | "agent.state_management"
  | "agent.tool_calling"
  | "agent.rag_fundamentals"
  | "agent.eval"
  | "agent.guardrail"
  | "agent.cost_latency"
  | "agent.production_reliability"

/**
 * Job requirement
 */
export interface JobRequirement {
  requirement_id: string
  competency_code: CompetencyCode
  title: string
  description: string | null
  importance: number // 0.0 - 1.0
  expected_level: number // 1-5
  evidence_expectation: string[] // List of expected evidence
}

/**
 * Job target
 */
export interface JobTarget {
  job_target_id: string
  title: string
  level: JobLevel
  interview_round: InterviewRound
  description: string | null
  source: JobTargetSource
  raw_jd: string | null
  requirements: JobRequirement[]
  created_at: string
}

/**
 * Create requirement request
 */
export interface RequirementCreateRequest {
  competency_code: CompetencyCode
  title: string
  description?: string
  importance: number // 0.0 - 1.0
  expected_level: number // 1-5
  evidence_expectation: string[] // Min 2 items
}

/**
 * Create job target request
 */
export interface JobTargetCreateRequest {
  title: string
  level: JobLevel
  interview_round?: InterviewRound
  description?: string
  source?: JobTargetSource
  raw_jd?: string
  requirements: RequirementCreateRequest[]
}

/**
 * Parse JD request
 */
export interface ParseJDRequest {
  jd_text: string
}

/**
 * Parse JD response
 */
export interface ParseJDResponse {
  requirements: RequirementCreateRequest[]
  inferred_level: JobLevel | null
  inferred_round: InterviewRound | null
}

/**
 * Update requirement request
 */
export interface RequirementUpdateRequest {
  title?: string
  description?: string
  importance?: number
  expected_level?: number
  evidence_expectation?: string[]
}

/**
 * Job target template
 */
export interface JobTargetTemplate {
  id: string
  title: string
  level: JobLevel
  description: string
  requirements: RequirementCreateRequest[]
}
