/**
 * Claim Gap API client
 */

import { api } from '@/lib/api-client';

// ============================================================
// Types
// ============================================================

export interface ClaimGapRequest {
  resume_id: string;
  job_target_id: string;
}

export interface GapResponse {
  gap_type: 'UNCOVERED_REQUIREMENT' | 'HIGH_PRIORITY_WEAK_EVIDENCE' | 'WEAK_EVIDENCE_CLAIM' | 'SUPPORTED_CLAIM' | 'IRRELEVANT_CLAIM';
  claim_id: string | null;
  requirement_id: string | null;
  competency_code: string;
  priority: number;
  reason_codes: string[];
  explanation: string;
  claim_text: string | null;
  requirement_title: string | null;
  requirement_importance: number | null;
  requirement_expected_level: number | null;
  claim_coverage_level: number | null;
}

export interface CoverageStatsResponse {
  total_requirements: number;
  covered_requirements: number;
  uncovered_requirements: number;
  weak_evidence_count: number;
  high_priority_gaps: number;
  coverage_percentage: number;
}

export interface InterviewTargetResponse {
  claim_id: string | null;
  requirement_id: string | null;
  competency_code: string;
  priority: number;
  reason_codes: string[];
  explanation: string;
  gap_type: string;
  claim_text: string | null;
  requirement_title: string | null;
}

export interface ClaimGapResponse {
  resume_id: string;
  job_target_id: string;
  gaps: GapResponse[];
  coverage_stats: CoverageStatsResponse;
  interview_plan: {
    total_targets: number;
    high_priority_count: number;
    targets: InterviewTargetResponse[];
  };
  high_priority_targets: string[];
}

// ============================================================
// API Functions
// ============================================================

export const claimGapApi = {
  /**
   * Analyze claim gap between resume and job target
   */
  analyze: async (data: ClaimGapRequest): Promise<ClaimGapResponse> => {
    const response = await api.post<ClaimGapResponse>('/claim-gap', data);
    return response.data;
  },

  /**
   * Get claim gap analysis
   */
  get: async (resumeId: string, jobTargetId: string): Promise<ClaimGapResponse> => {
    const response = await api.get<ClaimGapResponse>(
      `/claim-gap/resume/${resumeId}/job-target/${jobTargetId}`
    );
    return response.data;
  },
};
