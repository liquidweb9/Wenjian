<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getResume, getClaims, confirmRevision, updateRevision, deleteResume } from '../api/index.js'
import { useInterviewStore } from '../stores/interview.js'

const route = useRoute()
const router = useRouter()
const store = useInterviewStore()

const resume = ref(null)
const claims = ref([])
const loading = ref(true)
const error = ref(null)

// Confirm dialog
const targetRole = ref('Software Engineer')
const confirming = ref(false)

// Edit mode
const editing = ref(false)
const editText = ref('')
const saving = ref(false)

// Interview
const creating = ref(false)

// Delete
const deleting = ref(false)

async function load() {
  loading.value = true
  error.value = null
  try {
    const [resR,claimsR] = await Promise.all([
      getResume(route.params.id),
      getClaims(route.params.id),
    ])
    resume.value = resR.data
    claims.value = claimsR.data.claims || []
    editText.value = ''
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function doConfirm() {
  confirming.value = true
  try {
    const { data } = await confirmRevision(route.params.id, resume.value.revision_id || resume.value.latest_revision, targetRole.value)
    resume.value = { ...resume.value, status: data.status }
    claims.value = data.claims || []
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    confirming.value = false
  }
}

async function doStartInterview() {
  creating.value = true
  try {
    await store.start(route.params.id, resume.value.revision_id, targetRole.value)
    router.push(`/interview/${store.current.interview_id}`)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    creating.value = false
  }
}

function startEdit() {
  editText.value = resume.value.normalized_text || ''
  editing.value = true
}

async function saveEdit() {
  saving.value = true
  try {
    await updateRevision(route.params.id, resume.value.revision_id, editText.value)
    resume.value.normalized_text = editText.value
    editing.value = false
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    saving.value = false
  }
}

async function doDelete() {
  if (!confirm('确定删除此简历及相关所有数据？此操作不可撤销。')) return
  deleting.value = true
  try {
    await deleteResume(route.params.id)
    router.push('/upload')
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    deleting.value = false
  }
}

function statusTag(s) {
  if (!s) return ''
  const m = { UPLOADED: 'tag-gray', PARSED_UNCONFIRMED: 'tag-yellow', CONFIRMED: 'tag-green', FAILED: 'tag-red' }
  return m[s] || 'tag-gray'
}
</script>

<template>
  <div v-if="loading" class="card"><p>加载中...</p></div>
  <div v-else-if="error" class="card" style="border-left:4px solid #e63946;"><p style="color:#e63946;">{{ error }}</p></div>
  <div v-else-if="resume" class="detail-page">
    <div class="flex" style="justify-content:space-between;align-items:center;">
      <h2>简历详情</h2>
      <button class="btn btn-danger btn-sm" :disabled="deleting" @click="doDelete">{{ deleting ? '删除中...' : '删除' }}</button>
    </div>

    <div class="card mt-1">
      <div class="flex gap-2" style="flex-wrap:wrap;">
        <div><span class="label">文件</span><div>{{ resume.file_name }}</div></div>
        <div><span class="label">类型</span><div>{{ resume.source_type }}</div></div>
        <div><span class="label">状态</span><div><span :class="['tag', statusTag(resume.status)]">{{ resume.status }}</span></div></div>
      </div>
    </div>

    <!-- Normalized text -->
    <div class="card mt-1">
      <div class="flex" style="justify-content:space-between;align-items:center;">
        <span class="label">规范化文本</span>
        <button v-if="!editing" class="btn btn-outline btn-sm" @click="startEdit">编辑</button>
      </div>
      <div v-if="editing">
        <textarea v-model="editText" rows="12" class="edit-area" style="width:100%;"></textarea>
        <div class="flex gap-1 mt-1">
          <button class="btn btn-primary btn-sm" :disabled="saving" @click="saveEdit">{{ saving ? '保存中...' : '保存' }}</button>
          <button class="btn btn-outline btn-sm" @click="editing = false">取消</button>
        </div>
      </div>
      <pre v-else class="text-preview">{{ resume.normalized_text || resume.raw_text || '(无内容)' }}</pre>
    </div>

    <!-- Claims (after confirm) -->
    <div v-if="claims.length > 0" class="card mt-1">
      <span class="label">技术主张 ({{ claims.length }})</span>
      <div v-for="c in claims" :key="c.claim_id" class="claim-row">
        <div class="flex" style="justify-content:space-between;">
          <strong style="font-size:0.9rem;">{{ c.data?.claim_text || c.claim_text }}</strong>
          <span :class="['tag', c.priority >= 70 ? 'tag-red' : c.priority >= 40 ? 'tag-yellow' : 'tag-blue']">
            优先级 {{ c.priority }}
          </span>
        </div>
        <div class="flex gap-1 mt-1" style="flex-wrap:wrap;">
          <span v-for="t in (c.data?.technologies || c.technologies || [])" :key="t" class="tag tag-blue">{{ t }}</span>
          <span v-for="rf in (c.data?.risk_flags || c.risk_flags || [])" :key="rf" class="tag tag-red">{{ rf }}</span>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="card mt-1">
      <span class="label">操作</span>
      <div class="flex gap-1 mt-1" style="flex-wrap:wrap;">
        <button v-if="resume.status !== 'CONFIRMED'" class="btn btn-success" :disabled="confirming" @click="doConfirm">
          {{ confirming ? '确认中...' : '确认并提取主张' }}
        </button>
        <button class="btn btn-primary" :disabled="creating || resume.status !== 'CONFIRMED'" @click="doStartInterview">
          {{ creating ? '创建中...' : (resume.status === 'CONFIRMED' ? '开始面试' : '请先确认简历') }}
        </button>
      </div>
      <div class="mt-1">
        <span class="label">目标岗位</span>
        <input v-model="targetRole" class="input" style="max-width:300px;" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-page { max-width: 720px; margin: 0 auto; }
.text-preview {
  background: #f9fafb;
  padding: 0.75rem;
  border-radius: 4px;
  font-size: 0.85rem;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 300px;
  overflow-y: auto;
  margin-top: 0.4rem;
}
.edit-area {
  font-family: inherit;
  padding: 0.5rem;
  border: 1px solid #d0d5dd;
  border-radius: 6px;
  outline: none;
  margin-top: 0.4rem;
}
.edit-area:focus { border-color: #4361ee; }
.claim-row {
  border-bottom: 1px solid #f0f0f0;
  padding: 0.75rem 0;
}
.claim-row:last-child { border-bottom: none; }
.input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d0d5dd;
  border-radius: 6px;
  outline: none;
  width: 100%;
}
.input:focus { border-color: #4361ee; }
</style>
