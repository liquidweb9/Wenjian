export const BRAND = {
  chineseName: "问鉴",
  englishName: "Wenjian",
  productName: "问鉴｜简历驱动的 AI 模拟面试平台",
  englishProductName: "Wenjian — Resume-grounded AI Interview Platform",
  tagline: "每一段简历，都值得被认真追问。",
  taglineEn: "Every experience deserves a deeper question.",
  summary:
    "基于你的真实经历生成个性化问题，通过连续追问、回答评分和证据分析，还原更接近真实面试的训练过程。",
  summaryEn:
    "Generate personalized questions from real resume experiences, conduct adaptive follow-up interviews, evaluate answers, and provide evidence-based feedback for more realistic interview practice.",
  description:
    "问鉴是一款简历驱动的 AI 模拟面试平台，基于真实经历生成个性化问题，通过连续追问、回答评分和证据分析，提供更接近真实面试的训练体验。",
  alt: "问鉴 Wenjian",
} as const

export const PAGE_TITLES: Record<string, string> = {
  "/login": "进入问鉴",
  "/app/dashboard": "工作台",
  "/app/resumes": "简历管理",
  "/app/resumes/new": "上传简历",
  "/app/interviews": "模拟面试",
  "/app/interviews/new": "创建模拟面试",
  "/app/analytics": "能力分析",
  "/app/settings": "设置",
}

export function getDocumentTitle(path: string, custom?: string) {
  const section = PAGE_TITLES[path] || custom
  return section ? `${section} | ${BRAND.chineseName} ${BRAND.englishName}` : BRAND.productName
}
