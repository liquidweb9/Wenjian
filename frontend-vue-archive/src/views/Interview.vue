<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useInterviewStore } from '../stores/interview.js'

const route = useRoute()
const router = useRouter()
const store = useInterviewStore()

const answerText = ref('')
const submitting = ref(false)
const error = ref(null)
const loaded = ref(false)
const answerListEl = ref(null)

onMounted(async () => {
  try {
    await store.loadState(route.params.id)
    loaded.value = true
  } catch (e) {
    error.value = '加载面试失败: ' + (e.response?.data?.detail || e.message)
  }
})

async function submit() {
  if (!answerText.value.trim() || !store.current) return
  submitting.value = true
  error.value = null
  const qid = store.current.current_question?.question_id || store.current.question_id
  try {
    await store.answer(qid, answerText.value)
    answerText.value = ''
    await nextTick()
    if (answerListEl.value) {
      answerListEl.value.scrollTop = answerListEl.value.scrollHeight
    }
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    submitting.value = false
  }
}

async function finishEarly() {
  if (!confirm('确定结束面试？')) return
  error.value = null
  try {
    await store.finish()
    router.push(`/report/${store.current.interview_id}`)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  }
}

function getScoreColor(score) {
  if (score >= 80) return '#2ec4b6'
  if (score >= 60) return '#f59e0b'
  return '#e63946'
}
</script>

<template>
  <div class="interview-page">
    <div v-if="error && !loaded" class="card" style="border-left:4px solid #e63946;"><p style="color:#e63946;">{{ error }}</p></div>

    <template v-else-if="loaded && store.current">
      <!-- Header -->
      <div class="flex" style="justify-content:space-between;align-items:center;">
        <h2>AI 面试</h2>
        <div class="flex gap-1" style="align-items:center;">
          <span class="tag tag-blue">第 {{ store.current.turn_count || 0 }} / {{ store.current.max_turns }} 轮</span>
          <span v-if="store.current.status" :class="['tag', store.current.status === 'finished' ? 'tag-green' : 'tag-yellow']">
            {{ store.current.status }}
          </span>
        </div>
      </div>

      <!-- Finished state -->
      <div v-if="store.current.finished || store.current.status === 'finished'" class="card mt-1" style="border-left:4px solid #2ec4b6; text-align:center;">
        <h3>✅ 面试已完成</h3>
        <button class="btn btn-primary mt-1" @click="router.push(`/report/${store.current.interview_id}`)">查看报告</button>
      </div>

      <!-- Q&A area -->
      <div v-else>
        <div ref="answerListEl" class="qa-list card mt-1">
          <div v-if="store.qaHistory.length === 0" style="color:#999;text-align:center;padding:1rem;">
            等待第一个问题...
          </div>
          <div v-for="(qa, i) in store.qaHistory" :key="i" class="qa-pair">
            <div class="q-bubble">
              <strong>Q{{ i+1 }}:</strong> {{ qa.questionId ? '' : '' }}
              <span v-if="qa.evaluation" class="score-badge" :style="{ background: getScoreColor(qa.evaluation.dimensions?.reduce((s,d)=>s+d.score,0)/(qa.evaluation.dimensions?.length||1)) }">
                {{ qa.evaluation.dimensions?.length ? (qa.evaluation.dimensions.reduce((s,d)=>s+d.score,0) / qa.evaluation.dimensions.length).toFixed(0) : '' }}
              </span>
            </div>
            <div class="a-bubble">{{ qa.answer }}</div>
            <div v-if="qa.coaching" class="coaching-bubble">
              <strong>教练反馈</strong>
              <div v-if="qa.coaching.score_summary" style="margin-bottom:0.3rem;">
                <span style="color:#4361ee;">📊</span> {{ qa.coaching.score_summary }}
              </div>
              <div v-if="qa.coaching.question_analysis" class="coaching-section">
                <div class="coaching-label">🎯 问题意图</div>
                <div class="coaching-text">{{ qa.coaching.question_analysis }}</div>
              </div>
              <div v-if="qa.coaching.what_was_good?.length" class="coaching-section">
                <div class="coaching-label">✅ 回答亮点</div>
                <div v-for="g in qa.coaching.what_was_good" :key="g" class="coaching-text">• {{ g }}</div>
              </div>
              <div v-if="qa.coaching.what_to_improve?.length" class="coaching-section">
                <div class="coaching-label">△ 改进空间</div>
                <div v-for="imp in qa.coaching.what_to_improve" :key="imp" class="coaching-text">• {{ imp }}</div>
              </div>
              <div v-if="qa.coaching.expert_answer" class="coaching-section">
                <div class="coaching-label">💡 参考回答</div>
                <div class="coaching-text" style="white-space:pre-wrap;">{{ qa.coaching.expert_answer }}</div>
              </div>
              <div v-if="qa.coaching.knowledge_gaps?.length" class="coaching-section">
                <div class="coaching-label">📚 知识缺口</div>
                <div class="coaching-text">{{ qa.coaching.knowledge_gaps.join('; ') }}</div>
              </div>
              <div v-if="qa.coaching.likely_follow_up_questions?.length" class="coaching-section">
                <div class="coaching-label">⏩ 可能的追问</div>
                <div v-for="fq in qa.coaching.likely_follow_up_questions.slice(0,3)" :key="fq" class="coaching-text">• {{ fq }}</div>
              </div>
            </div>
          </div>
          <div v-if="store.loading" class="loading-indicator">
            <span class="dot-pulse"></span> AI 思考中...
          </div>
        </div>

        <!-- Current question -->
        <div v-if="store.current.current_question || store.current.next_question" class="card current-q">
          <div class="q-label">当前问题</div>
          <p class="q-text">
            {{ store.current.current_question?.question_text || store.current.next_question }}
          </p>
        </div>

        <!-- Answer input -->
        <div class="card answer-box">
          <textarea
            v-model="answerText"
            rows="4"
            class="answer-input"
            placeholder="输入你的回答..."
            :disabled="submitting || store.current.finished"
            @keydown.ctrl.enter="submit"
          ></textarea>
          <div class="flex gap-1 mt-1" style="justify-content:space-between;">
            <button class="btn btn-primary" :disabled="!answerText.trim() || submitting || store.loading" @click="submit">
              {{ submitting ? '提交中...' : '提交回答 (Ctrl+Enter)' }}
            </button>
            <button class="btn btn-outline btn-sm" @click="finishEarly">结束面试</button>
          </div>
          <div v-if="error" class="mt-1" style="color:#e63946;font-size:0.85rem;">{{ error }}</div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.interview-page { max-width: 720px; margin: 0 auto; }
.qa-list { max-height: 400px; overflow-y: auto; margin-bottom: 1rem; }
.qa-pair { margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid #f0f0f0; }
.qa-pair:last-child { border-bottom: none; }
.q-bubble {
  background: #eef2ff;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  font-size: 0.85rem;
  margin-bottom: 0.4rem;
}
.a-bubble {
  background: #f9fafb;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  font-size: 0.85rem;
  white-space: pre-wrap;
}
.coaching-bubble {
  background: #fffbeb;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  font-size: 0.8rem;
  margin-top: 0.4rem;
}
.coaching-section {
  margin-top: 0.5rem;
}
.coaching-label {
  font-weight: 600;
  font-size: 0.78rem;
  margin-bottom: 0.15rem;
}
.coaching-text {
  font-size: 0.78rem;
  line-height: 1.5;
  margin-bottom: 0.15rem;
}
.score-badge {
  float: right;
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
  color: #fff;
  font-size: 0.75rem;
  font-weight: 600;
}
.current-q { border-left: 4px solid #4361ee; margin-bottom: 1rem; }
.q-label { font-size: 0.75rem; font-weight: 600; color: #4361ee; text-transform: uppercase; }
.q-text { font-size: 1rem; margin-top: 0.3rem; }
.answer-box { }
.answer-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d0d5dd;
  border-radius: 6px;
  outline: none;
  resize: vertical;
  font-family: inherit;
}
.answer-input:focus { border-color: #4361ee; }
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  color: #666;
  font-size: 0.85rem;
}
.dot-pulse {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #4361ee;
  animation: pulse 1s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
</style>
