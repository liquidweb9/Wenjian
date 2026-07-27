<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { uploadResumeFile, uploadResumeText } from '../api/index.js'

const router = useRouter()
const tab = ref('file')
const uploading = ref(false)
const error = ref(null)
const result = ref(null)

// File upload
const selectedFile = ref(null)
function onFileChange(e) {
  selectedFile.value = e.target.files[0] || null
}

async function doUploadFile() {
  if (!selectedFile.value) return
  uploading.value = true
  error.value = null
  try {
    const { data } = await uploadResumeFile(selectedFile.value)
    result.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    uploading.value = false
  }
}

// Text upload
const textName = ref('resume.txt')
const textContent = ref('')

async function doUploadText() {
  if (!textContent.value.trim()) return
  uploading.value = true
  error.value = null
  try {
    const { data } = await uploadResumeText(textName.value, textContent.value)
    result.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    uploading.value = false
  }
}

function goToResume() {
  router.push(`/resumes/${result.value.resume_id}`)
}

function reset() {
  result.value = null
  selectedFile.value = null
  textContent.value = ''
  error.value = null
}
</script>

<template>
  <div class="upload-page">
    <h2>上传简历</h2>
    <p class="mb-2" style="color:#666;font-size:0.9rem;">上传简历文件或粘贴文本，系统将自动解析提取结构化信息。</p>

    <div v-if="result" class="card result-card">
      <h3>✅ 解析完成</h3>
      <div class="flex gap-2 mt-1" style="flex-wrap:wrap;">
        <div><span class="label">文件</span><div>{{ result.file_name || textName }}</div></div>
        <div><span class="label">类型</span><div>{{ result.source_type }}</div></div>
        <div><span class="label">解析质量</span><div>{{ (result.extraction_quality * 100).toFixed(0) }}%</div></div>
        <div><span class="label">识别段落</span><div>{{ result.blocks?.length || 0 }} 块</div></div>
        <div><span class="label">状态</span><div><span class="tag tag-yellow">{{ result.status }}</span></div></div>
      </div>
      <div v-if="result.extraction_warnings?.length" class="mt-1">
        <span class="label">警告</span>
        <div v-for="w in result.extraction_warnings" :key="w" class="tag tag-red" style="margin-right:0.3rem;">{{ w }}</div>
      </div>
      <div class="mt-2 flex gap-1">
        <button class="btn btn-primary" @click="goToResume">查看详情 →</button>
        <button class="btn btn-outline" @click="reset">重新上传</button>
      </div>
    </div>

    <div v-else class="card">
      <div class="tabs mb-2">
        <button :class="['tab', { active: tab === 'file' }]" @click="tab = 'file'">上传文件</button>
        <button :class="['tab', { active: tab === 'text' }]" @click="tab = 'text'">粘贴文本</button>
      </div>

      <div v-if="tab === 'file'">
        <input type="file" accept=".pdf,.txt,.tex" @change="onFileChange" class="file-input" />
        <p style="font-size:0.8rem;color:#888;margin-top:0.3rem;">支持 PDF、TXT、TEX 格式，最大 5MB</p>
        <button class="btn btn-primary mt-1" :disabled="!selectedFile || uploading" @click="doUploadFile">
          {{ uploading ? '上传中...' : '上传' }}
        </button>
      </div>

      <div v-else>
        <div class="mb-1">
          <span class="label">文件名</span>
          <input v-model="textName" class="input" placeholder="resume.txt" />
        </div>
        <div class="mb-1">
          <span class="label">简历文本</span>
          <textarea v-model="textContent" rows="10" class="input" placeholder="在此粘贴简历内容..."></textarea>
        </div>
        <button class="btn btn-primary" :disabled="!textContent.trim() || uploading" @click="doUploadText">
          {{ uploading ? '解析中...' : '解析文本' }}
        </button>
      </div>

      <div v-if="error" class="mt-1" style="color:#e63946;font-size:0.85rem;">{{ error }}</div>
    </div>
  </div>
</template>

<style scoped>
.upload-page { max-width: 640px; margin: 0 auto; }
.tabs { display: flex; gap: 0; border-bottom: 2px solid #e5e7eb; }
.tab {
  padding: 0.5rem 1rem;
  border: none;
  background: none;
  font-weight: 500;
  color: #666;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}
.tab.active { color: #4361ee; border-bottom-color: #4361ee; }
.file-input { display: block; padding: 0.5rem 0; }
.input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d0d5dd;
  border-radius: 6px;
  outline: none;
}
.input:focus { border-color: #4361ee; }
textarea.input { resize: vertical; }
.result-card { border-left: 4px solid #2ec4b6; }
</style>
