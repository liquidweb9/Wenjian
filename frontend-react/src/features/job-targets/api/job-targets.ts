/**
 * Job Target API client
 */

import { api } from '@/lib/api-client';

// ============================================================
// Types
// ============================================================

export interface RequirementCreate {
  competency_code: string;
  title: string;
  description?: string;
  importance: number;
  expected_level: number;
  evidence_expectation: string[];
}

export interface RequirementResponse {
  requirement_id: string;
  competency_code: string;
  title: string;
  description: string | null;
  importance: number;
  expected_level: number;
  evidence_expectation: string[];
}

export interface JobTargetCreate {
  title: string;
  level: 'intern' | 'junior' | 'mid' | 'senior' | 'staff';
  interview_round: 'resume' | 'project' | 'technical' | 'system_design';
  description?: string;
  source: 'template' | 'pasted_jd' | 'manual';
  raw_jd?: string;
  requirements: RequirementCreate[];
}

export interface JobTargetResponse {
  job_target_id: string;
  title: string;
  level: string;
  interview_round: string;
  description: string | null;
  source: string;
  raw_jd: string | null;
  requirements: RequirementResponse[];
  created_at: string;
}

export interface ParseJDRequest {
  jd_text: string;
}

export interface ParseJDResponse {
  requirements: RequirementCreate[];
  inferred_level: string | null;
  inferred_round: string | null;
}

// ============================================================
// API Functions
// ============================================================

export const jobTargetApi = {
  /**
   * Create a new job target
   */
  create: async (data: JobTargetCreate): Promise<JobTargetResponse> => {
    const response = await api.post<JobTargetResponse>('/job-targets', data);
    return response.data;
  },

  /**
   * Get a job target by ID
   */
  get: async (jobTargetId: string): Promise<JobTargetResponse> => {
    const response = await api.get<JobTargetResponse>(`/job-targets/${jobTargetId}`);
    return response.data;
  },

  /**
   * List all job targets
   */
  list: async (params?: { level?: string }): Promise<JobTargetResponse[]> => {
    const response = await api.get<JobTargetResponse[]>('/job-targets', { params });
    return response.data;
  },

  /**
   * Parse JD text to extract requirements
   */
  parseJD: async (jobTargetId: string, data: ParseJDRequest): Promise<ParseJDResponse> => {
    const response = await api.post<ParseJDResponse>(
      `/job-targets/${jobTargetId}/parse-jd`,
      data
    );
    return response.data;
  },
};
