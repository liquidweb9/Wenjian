<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useInterviewStore } from '../stores/interview.js'

const route = useRoute()
const router = useRouter()
const store = useInterviewStore()

const loading = ref(true)
const error = ref(null)
const interviewMeta = ref(null)

onMounted(async () => {
  try {
    await store.loadState(route.params.id)
    await store.loadReport(route.params.id)
    interviewMeta.value = store.current
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
})

function safe(val, def = '-') { return val ?? def }

function renderReportText(text) {
  if (!text) return ''
  // Simple markdown-like rendering: preserve line breaks, detect sections
  return text
    .replace(/^### (.+)$/gm, '─── $1 ───')
    .replace(/^## (.+)$/gm, '═══ $1 ═══')
    .replace(/^# (.+)$/gm, '▓▓▓ $1 ▓▓▓')
}
</script>

<template>
  <div class="report-page">
    <div class="flex" style="justify-content:space-between;align-items:center;">
      <h2>面试报告</h2>
      <router-link to="/" class="btn btn-outline btn-sm">返回首页</router-link>
    </div>

    <div v-if="loading" class="card mt-1"><p>加载报告...</p></div>
    <div v-else-if="error" class="card mt-1" style="border-left:4px solid #e63946;"><p style="color:#e63946;">{{ error }}</p></div>
    <div v-else>
      <!-- Meta info -->
      <div class="card mt-1">
        <div class="flex gap-2" style="flex-wrap:wrap;">
          <div><span class="label">面试 ID</span><div style="font-size:0.85rem;">{{ interviewMeta?.interview_id }}</div></div>
          <div><span class="label">状态</span><div><span class="tag tag-green">{{ interviewMeta?.status }}</span></div></div>
          <div><span class="label">轮次</span><div>{{ interviewMeta?.turn_count || 0 }} / {{ interviewMeta?.max_turns }}</div></div>
        </div>
      </div>

      <!-- Report summary -->
      <div v-if="store.reportData?.report" class="card mt-1 report-content">
        <div v-if="store.reportData.report.summary" class="summary-section">
          <h3>评分摘要</h3>
          <div class="score-display">
            <div class="score-circle">
              <span class="score-num">{{ safe(store.reportData.report.summary.overall_score) }}</span>
              <span class="score-label">总分</span>
            </div>
            <div class="score-stats">
              <div>问题总数: <strong>{{ safe(store.reportData.report.summary.total_questions) }}</strong></div>
              <div>已验证主张: <strong>{{ safe(store.reportData.report.summary.claims_verified) }}</strong></div>
              <div>发现矛盾: <strong>{{ safe(store.reportData.report.summary.contradictions_found) }}</strong></div>
            </div>
          </div>
        </div>

        <!-- Report text -->
        <div v-if="store.reportData.report.report_text" class="text-section">
          <h3>详细报告</h3>
          <pre class="report-text">{{ store.reportData.report.report_text }}</pre>
        </div>
        <div v-else>
          <pre class="report-text">{{ JSON.stringify(store.reportData.report, null, 2) }}</pre>
        </div>
      </div>

      <div v-else class="card mt-1" style="border-left:4px solid #f59e0b;">
        <h3>⏳ 报告生成中</h3>
        <p style="color:#666;">面试报告尚未生成，或后端仍在处理。请稍后再试。</p>
        <button class="btn btn-primary btn-sm mt-1" @click="router.go(0)">刷新</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.report-page { max-width: 720px; margin: 0 auto; }
.report-content { }
.summary-section { margin-bottom: 1.5rem; }
.score-display { display: flex; gap: 2rem; align-items: center; margin-top: 0.75rem; }
.score-circle {
  width: 80px; height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4361ee, #2ec4b6);
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.score-num { font-size: 1.5rem; font-weight: 700; line-height: 1; }
.score-label { font-size: 0.65rem; opacity: 0.9; }
.score-stats { font-size: 0.85rem; }
.score-stats div { margin-bottom: 0.3rem; }
.text-section { }
.text-section h3 { margin-bottom: 0.5rem; }
.report-text {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 6px;
  font-size: 0.85rem;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 600px;
  overflow-y: auto;
}
</style>
