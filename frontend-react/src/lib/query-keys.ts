// eslint-disable-next-line @typescript-eslint/no-explicit-any
type FilterParams = Record<string, any>

export const queryKeys = {
  resumes: {
    all: ["resumes"] as const,
    list: (filters: FilterParams = {}) => ["resumes", "list", filters] as const,
    detail: (resumeId: string) => ["resumes", "detail", resumeId] as const,
    claims: (resumeId: string) => ["resumes", resumeId, "claims"] as const,
    revisions: (resumeId: string) => ["resumes", resumeId, "revisions"] as const,
  },
  interviews: {
    all: ["interviews"] as const,
    list: (filters: FilterParams = {}) => ["interviews", "list", filters] as const,
    detail: (id: string) => ["interviews", "detail", id] as const,
    report: (id: string) => ["interviews", id, "report"] as const,
  },
  dashboard: {
    summary: ["dashboard", "summary"] as const,
  },
  analytics: {
    summary: ["analytics", "summary"] as const,
    trends: ["analytics", "trends"] as const,
  },
  evidence: {
    all: ["evidence"] as const,
    verificationPoints: (claimId: string) => ["evidence", "verification-points", claimId] as const,
    transitions: (verificationPointId: string) => ["evidence", "transitions", verificationPointId] as const,
    contradictions: (interviewId: string, status?: string) => {
      const base = ["evidence", "contradictions", interviewId] as const
      return status ? ([...base, status] as const) : base
    },
    evidence: (verificationPointId: string) => ["evidence", "evidence", verificationPointId] as const,
  },
}
