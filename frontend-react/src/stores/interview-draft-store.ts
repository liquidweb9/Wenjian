import { create } from "zustand"
import { persist } from "zustand/middleware"

interface InterviewDraftState {
  drafts: Record<string, string>
  pendingSubmissions: Record<string, string>
  setDraft: (interviewId: string, questionId: string, value: string) => void
  clearDraft: (interviewId: string, questionId: string) => void
  setPendingSubmission: (interviewId: string, questionId: string, idempotencyKey: string) => void
  clearPendingSubmission: (interviewId: string, questionId: string) => void
  clearAllDrafts: () => void
}

export const useInterviewDraftStore = create<InterviewDraftState>()(
  persist(
    (set) => ({
      drafts: {},
      pendingSubmissions: {},
      setDraft: (interviewId, questionId, value) =>
        set((s) => ({
          drafts: { ...s.drafts, [`${interviewId}_${questionId}`]: value },
        })),
      clearDraft: (interviewId, questionId) => {
        set((s) => {
          const drafts = { ...s.drafts }
          delete drafts[`${interviewId}_${questionId}`]
          return { drafts }
        })
      },
      setPendingSubmission: (interviewId, questionId, idempotencyKey) =>
        set((s) => ({
          pendingSubmissions: {
            ...s.pendingSubmissions,
            [`${interviewId}_${questionId}`]: idempotencyKey,
          },
        })),
      clearPendingSubmission: (interviewId, questionId) =>
        set((s) => {
          const pendingSubmissions = { ...s.pendingSubmissions }
          delete pendingSubmissions[`${interviewId}_${questionId}`]
          return { pendingSubmissions }
        }),
      clearAllDrafts: () => set({ drafts: {}, pendingSubmissions: {} }),
    }),
    { name: "interview-drafts" },
  ),
)
