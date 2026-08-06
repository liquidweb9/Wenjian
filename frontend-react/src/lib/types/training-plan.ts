/**
 * Training plan types for Phase 2.4.
 */

export type TrainingTaskStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "DISMISSED"

/** A training task generated from evidence gaps. */
export interface TrainingTask {
  task_id: string
  task_type: string
  competency_code: string
  title: string
  description: string
  /** The generator emits a dict, but legacy rows may carry a list. */
  completion_criteria: Record<string, unknown> | unknown[]
  status: TrainingTaskStatus
  priority: number
  resume_id: string
  interview_id: string
  created_at: string | null
  completed_at: string | null
}

/** Result of listing or generating tasks. */
export interface TrainingTaskResult {
  tasks: TrainingTask[]
}
