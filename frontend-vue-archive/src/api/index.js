import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
})

export default api

// --- Resumes ---
export function uploadResumeFile(file) {
  const form = new FormData()
  form.append('file', file)
  return api.post('/resumes', form)
}

export function uploadResumeText(fileName, text) {
  return api.post('/resumes/text', { file_name: fileName, text })
}

export function getResume(id) {
  return api.get(`/resumes/${id}`)
}

export function getClaims(resumeId) {
  return api.get(`/resumes/${resumeId}/claims`)
}

export function updateRevision(resumeId, revisionId, normalizedText) {
  return api.patch(`/resumes/${resumeId}/revisions/${revisionId}`, { normalized_text: normalizedText })
}

export function confirmRevision(resumeId, revisionId, targetRole = '') {
  return api.post(`/resumes/${resumeId}/revisions/${revisionId}/confirm?target_role=${encodeURIComponent(targetRole)}`)
}

export function deleteResume(id) {
  return api.delete(`/resumes/${id}`)
}

// --- Interviews ---
export function createInterview(resumeId, revisionId, targetRole, options = {}) {
  return api.post('/interviews', {
    resume_id: resumeId,
    resume_revision_id: revisionId,
    target_role: targetRole,
    job_description: options.jobDescription || null,
    mode: options.mode || 'simulation',
    max_turns: options.maxTurns || 15,
  })
}

export function getInterview(id) {
  return api.get(`/interviews/${id}`)
}

export function submitAnswer(interviewId, questionId, answerText, idempotencyKey = null) {
  return api.post(`/interviews/${interviewId}/answers`, {
    question_id: questionId,
    answer_text: answerText,
    idempotency_key: idempotencyKey,
  })
}

export function finishInterview(interviewId) {
  return api.post(`/interviews/${interviewId}/finish`)
}

export function getReport(interviewId) {
  return api.get(`/interviews/${interviewId}/report`)
}
