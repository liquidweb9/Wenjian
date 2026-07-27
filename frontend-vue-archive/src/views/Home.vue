<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/index.js'

const router = useRouter()
const health = ref(null)
const error = ref(null)

onMounted(async () => {
  try {
    const { data } = await api.get('/health')
    health.value = data
  } catch (e) {
    error.value = '后端服务不可用，请确认 API 服务已启动'
  }
})
</script>

<template>
  <div class="home">
    <div class="hero">
      <h1>简历深度面试系统</h1>
      <p class="subtitle">上传简历 → 解析提取技术主张 → AI 深度面试 → 评分报告</p>
      <div class="hero-actions">
        <router-link to="/upload" class="btn btn-primary">开始上传简历</router-link>
      </div>
    </div>

    <div v-if="error" class="card mt-2" style="border-left:4px solid #e63946;">
      <p style="color:#e63946;">{{ error }}</p>
    </div>
    <div v-else-if="health" class="card mt-2" style="border-left:4px solid #2ec4b6;">
      <p>✅ 后端服务运行中 · 环境: {{ health.env || 'unknown' }} · 模型: {{ health.model || 'unknown' }}</p>
    </div>
    <div v-else class="card mt-2">
      <p>⏳ 正在连接后端服务...</p>
    </div>

    <div class="steps mt-2">
      <div class="step card">
        <div class="step-num">1</div>
        <h3>上传简历</h3>
        <p>支持 PDF、TXT、TEX 格式，也可直接粘贴文本</p>
      </div>
      <div class="step card">
        <div class="step-num">2</div>
        <h3>确认解析</h3>
        <p>检查解析结果，确认后系统自动提取技术主张</p>
      </div>
      <div class="step card">
        <div class="step-num">3</div>
        <h3>AI 面试</h3>
        <p>基于简历主张进行多轮深度技术面试</p>
      </div>
      <div class="step card">
        <div class="step-num">4</div>
        <h3>获取报告</h3>
        <p>查看面试评分、分析、改进建议</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home { max-width: 720px; margin: 0 auto; }
.hero { text-align: center; padding: 2rem 0; }
.hero h1 { font-size: 1.8rem; margin-bottom: 0.5rem; }
.subtitle { color: #666; margin-bottom: 1.5rem; }
.hero-actions { display: flex; gap: 0.75rem; justify-content: center; }
.steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; }
.step { text-align: center; }
.step-num {
  width: 36px; height: 36px; border-radius: 50%;
  background: #4361ee; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; margin: 0 auto 0.5rem;
}
.step h3 { font-size: 0.95rem; margin-bottom: 0.3rem; }
.step p { font-size: 0.8rem; color: #666; }
</style>
