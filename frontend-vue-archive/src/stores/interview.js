import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createInterview, submitAnswer, finishInterview, getInterview, getReport } from '../api/index.js'

export const useInterviewStore = defineStore('interview', () => {
  const current = ref(null)
  const qaHistory = ref([])
  const reportData = ref(null)
  const loading = ref(false)

  async function start(resumeId, revisionId, targetRole, opts = {}) {
    loading.value = true
    try {
      const { data } = await createInterview(resumeId, revisionId, targetRole, opts)
      current.value = data
      qaHistory.value = []
      reportData.value = null
      return data
    } finally {
      loading.value = false
    }
  }

  async function answer(questionId, text) {
    if (!current.value) return
    loading.value = true
    try {
      const key = `${current.value.interview_id}_${Date.now()}`
      const { data } = await submitAnswer(current.value.interview_id, questionId, text, key)
      qaHistory.value.push({ questionId, answer: text, evaluation: data.evaluation, analysis: data.analysis, coaching: data.coaching })
      current.value = {
        ...current.value,
        status: data.status,
        turn_count: data.turn_count,
        current_question: data.current_question || current.value.current_question,
        next_question: data.next_question,
        next_question_id: data.next_question_id,
      }
      if (data.finished) current.value.finished = true
      return data
    } finally {
      loading.value = false
    }
  }

  async function finish() {
    if (!current.value) return
    loading.value = true
    try {
      const { data } = await finishInterview(current.value.interview_id)
      current.value.finished = true
      current.value.status = 'finished'
      // Load report
      const reportResp = await getReport(current.value.interview_id)
      reportData.value = reportResp.data
      return data
    } finally {
      loading.value = false
    }
  }

  async function loadState(id) {
    loading.value = true
    try {
      const { data } = await getInterview(id)
      current.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function loadReport(id) {
    const { data } = await getReport(id)
    reportData.value = data
    return data
  }

  const isActive = computed(() => current.value && !current.value.finished)

  return { current, qaHistory, reportData, loading, start, answer, finish, loadState, loadReport, isActive }
})
