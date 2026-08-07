<div align="center">
  <img src="./frontend-react/src/assets/brand/wenjian-mark.svg" width="150" alt="问鉴 Wenjian Logo" />
  <h1>问鉴 · Wenjian</h1>
  <p><strong>不止是“问过什么”，更要鉴别“你是否真的做过”。</strong></p>
  <p>
    一款以简历事实为起点、以证据验证为主线的 AI 深度面试平台。<br />
    它会理解你的项目，沿着回答继续追问，并把每一次判断沉淀为可解释的能力证据。
  </p>

  <p>
    <img alt="Python 3.12+" src="https://img.shields.io/badge/Python-3.12%2B-0D1B2A?style=flat-square&logo=python&logoColor=white" />
    <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.115%2B-0EA5A0?style=flat-square&logo=fastapi&logoColor=white" />
    <img alt="LangGraph" src="https://img.shields.io/badge/Agent-LangGraph-22C1C3?style=flat-square" />
    <img alt="React 19" src="https://img.shields.io/badge/React-19-0D1B2A?style=flat-square&logo=react&logoColor=61DAFB" />
    <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5.6%2B-0EA5A0?style=flat-square&logo=typescript&logoColor=white" />
    <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16-22C1C3?style=flat-square&logo=postgresql&logoColor=white" />
  </p>
</div>

---

## 为什么是「问鉴」？

传统题库只知道下一道题是什么，通用聊天机器人则很容易停留在宽泛建议。问鉴选择了一条更难、也更有价值的路径：

> 从简历中的真实项目出发，持续追踪技术细节、个人贡献、架构权衡和生产经验，直到一个主张被证实、被质疑，或需要更多证据。

系统不会机械地问满固定的 15 道题。每轮回答后，Agent 都会结合当前深度、回答质量、未解决矛盾、项目覆盖度与 Claim 状态，在”继续深挖、澄清回答、提高难度、切换项目、结束面试”之间作出确定性决策。

除了简历驱动的连续追问，问鉴还实现了职位对齐的完整训练闭环：JD 解析与能力需求匹配、证据状态机追踪、跨会话能力档案和结构化训练计划生成。

## ✨ 核心体验

### 🎯 职位驱动的能力验证

不只是"简历驱动"，更是"职位对齐"：
- **JD 解析与需求匹配**：解析职位描述，映射到能力目录，识别简历与职位的覆盖缺口
- **证据状态机**：每个验证点从 UNSEEN → ADDRESSED → PARTIALLY_SUPPORTED → VERIFIED，可追溯到具体问答
- **跨会话能力档案**：聚合多次面试的观察，计算能力稳定性（LOW/MEDIUM/HIGH）和迁移能力
- **结构化训练计划**：基于证据缺口生成可操作的训练任务（补充证据、复习概念、实战练习）

### 🧭 简历驱动，而非随机出题

支持 PDF、TXT、TEX 简历解析与人工确认，生成结构化 Profile，并提取可验证的 Resume Claims。问题围绕候选人的项目与职责组织，不是关键词拼接出来的题库。

### 🧠 会追问的 Agent Loop

基于 LangGraph 构建 11 节点状态机，通过七级深度模型从背景职责逐步走向代码接口、故障边界、架构权衡与反事实演进。LLM 负责理解和生成，代码规则掌控关键路由，使流程可追踪、可恢复、可测试。

### 🔎 证据化分析与六维评分

每次回答都会经历内容分析、证据核验与加权评分，覆盖：

| 维度 | 权重 | 想看见的能力 |
| --- | ---: | --- |
| 技术正确性 | 25% | 概念、原理与事实是否准确 |
| 实现深度 | 20% | 是否真正理解代码、接口与数据流 |
| 架构与权衡 | 15% | 是否能解释选择及其代价 |
| 个人贡献 | 15% | 能否区分“团队做了”与“我做了” |
| 生产意识 | 15% | 是否考虑故障、监控、性能和恢复 |
| 表达清晰度 | 10% | 能否结构化地说明复杂问题 |

### 💡 不只评分，还给出「预期回答」

每题不仅展示分数与分析，还提供考察意图、改进建议、回答框架、知识缺口、可能追问，以及一份更强的预期回答示例。目标不是给候选人贴标签，而是让下一次回答真正变好。

### ⚡ 面向长耗时任务的实时体验

前端通过 SSE 接收面试初始化、问题生成、答案分析、评分、教练反馈和报告生成等阶段事件；加载界面展示真实处理阶段与等待时间。断线自动重连、状态快照、轮询兜底与本地草稿共同降低刷新或退出重进造成的内容丢失风险。

### 📊 从单题反馈到完整能力画像

面试结束后生成多视图报告，汇总能力维度、项目与 Claim 验证状态、优势、风险、证据链和学习建议，并提供 Dashboard、趋势和分析视图。

**报告能力增强**：
- **Claim Passport**：每个 Claim 的验证状态时间线，链接到具体证据
- **JD Coverage**：职位需求的覆盖率分析（已覆盖/弱证据/未覆盖）
- **能力稳定性评分**：基于多轮面试、不同问题形式的稳定性判断
- **训练任务推荐**：从证据缺口生成的结构化任务列表

## 🪄 一次完整面试如何发生

<img src=./fig/wenjian_procedure.png>

## 🧩 技术架构

| 层级 | 主要技术 | 职责 |
| --- | --- | --- |
| Web | React 19、TypeScript、Vite、Tailwind CSS 4 | 面试工作台、简历管理、报告与分析 |
| Client State | TanStack Query、Zustand、LocalStorage | 服务端状态、交互状态和回答草稿恢复 |
| API | FastAPI、Pydantic、SSE | REST 接口、结构化契约与实时事件 |
| Agent | LangGraph、规则路由、LLM Gateway | 问题生成、分析、评分、证据与决策循环 |
| Data | SQLAlchemy 2 Async、PostgreSQL、Checkpoint | 简历、问答、评价、报告和执行状态持久化 |
| Quality | Pytest、Ruff、TypeScript、ESLint | 后端测试、静态检查与前端构建验证 |

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Node.js 22+
- pnpm
- PostgreSQL 16
- 一个 OpenAI-compatible LLM API Key

### 1. 启动数据库

```bash
docker compose up -d db
```

### 2. 配置并启动后端

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

pip install -e ".[dev]"
cp config.env.example config.env
```

Windows PowerShell 可使用：

```powershell
Copy-Item config.env.example config.env
```

编辑 `config.env`，至少填写：

```env
LLM_API_KEY=replace-with-your-api-key
LLM_BASE_URL=https://your-openai-compatible-endpoint/v1
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/resume_interview
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@localhost:5432/resume_interview
```

运行迁移并启动 API：

```bash
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. 启动前端

```bash
cd frontend-react
pnpm install
pnpm dev
```

访问：

- Web UI：<http://localhost:5174>
- OpenAPI / Swagger UI：<http://localhost:8000/docs>
- API 基础路径：`/api/v1`

> [!IMPORTANT]
> `config.env` 与前端 `.env` 已被 Git 忽略。请只提交 `.env.example` 模板，不要把 API Key、数据库密码或私钥写入仓库。

## 📚 深入了解

如果你想了解的不只是“能不能跑”，而是“它为什么这样设计”，可以从这里开始：

| 文档 | 内容 |
| --- | --- |
| [项目文档导航](./docs/README.md) | 完整文档入口与当前技术栈 |
| [当前实现与产品效果](./docs/current-implementation.md) | 已完成链路、鉴权、岗位目标、证据、能力档案、训练计划、持久化与当前边界 |
| [API 接口与预期返回](./docs/api-reference.md) | REST API、请求参数、响应示例、错误格式与 SSE 事件 |
| [Agent Loop 与决策机制](./docs/agent-loop.md) | 11 节点状态机、七级深度、暂停恢复与切换项目规则 |
| [React 前端页面与交互](./docs/frontend-pages.md) | 页面路由、面试工作台、加载体验、刷新恢复与视觉系统 |

## 🗂️ 项目结构

```text
.
├── app/
│   ├── api/v1/              # FastAPI 接口、鉴权、SSE 与报告
│   ├── interview/           # LangGraph、节点、路由与评分
│   ├── resume/              # Profile / Claim 构建与排序
│   ├── parsers/             # PDF / TXT / TEX 解析
│   ├── llm/                 # 模型路由、重试与 Token 预算
│   ├── job_target/          # 岗位目标、JD 解析与能力目录
│   ├── planning/            # Claim 与岗位映射、缺口分析、面试计划
│   ├── evidence/            # 证据状态机、验证点、矛盾与证据片段
│   ├── abilities/           # 跨场次能力观察、聚合与稳定性计算
│   ├── persistence/         # 数据模型、仓储与 Checkpoint
│   └── observability/       # 日志、指标与追踪
├── frontend-react/          # React 19 主前端
├── migrations/              # Alembic 数据库迁移
├── prompts/                 # 结构化提示词
├── evals/                   # 评估资产与回归测试
├── tests/                   # 后端测试
└── docs/                    # 产品、接口、Agent 与前端文档
```

## 🧪 开发与验证

**当前测试状态**（2026-08-07）：
- ✅ 599/599 测试通过（100%）
- ✅ 全部业务链路测试通过（简历、面试、岗位目标、证据、能力档案、训练计划）
- ✅ 所有接口强制用户属主校验（含 Dashboard / Analytics 按用户隔离）
- ✅ 前端 type-check（0 error）、ESLint、生产构建通过

```bash
# 后端测试与覆盖率
pytest tests/ -v
pytest tests/ --cov=app

# Python 静态检查
ruff check app tests

# 前端检查与生产构建
cd frontend-react
pnpm type-check
pnpm lint
pnpm build
```

## 🌱 项目愿景

问鉴希望把 AI 面试从“自动念题”推进到真正的证据驱动评估：

- 对候选人，它是一面能指出知识缺口、也能给出改进路径的镜子。
- 对面试官，它是一套可审查的追问逻辑、评分依据与项目证据链。
- 对 Agent 开发者，它是一个包含状态机、结构化输出、实时事件、持久化恢复和长任务 UX 的完整工程样本。

如果这个方向也让你感兴趣，欢迎阅读文档、运行项目、提出 Issue，或一起把下一次技术面试做得更深入、更公平、更有帮助。

---

<div align="center">
  <strong>Wenjian · Ask deeper. Verify with evidence.</strong><br />
  <sub>以问求真，以鉴见深。</sub>
</div>
