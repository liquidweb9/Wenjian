# 修复：反馈分阶段显示从未推进（一直停留在第一阶段）

日期：2026-08-07

## 现象

提交回答后进入分析阶段，页面顶部「问鉴正在分阶段整理本题反馈」的四步进度条
（理解回答 / 证据核验 / 多维评分 / 预期回答）一直停留在第一步，从不推进。

## 根因

`POST /api/v1/interviews/{id}/answers` 使用 `interview_graph.ainvoke()` 一次跑完
整张图（analyze → score → update_evidence → coaching → decide → question），
等整张图结束后才一次性批量发布全部 SSE 事件。因此：

1. 长时间分析期间前端只收到 `answer.accepted`，`analysis.completed` /
   `scoring.completed` / `coaching.ready` 都在最末尾同时到达。
2. `question.ready` 是最后一条，`event-reducer` 在处理它时把
   `latestEvaluation` / `latestCoaching` 立刻清空并切到 `answering`，
   用户根本来不及看到评分与反馈面板。
3. 前端 `AnalysisProgress` 第一步 `done: true` 写死，其余步骤依赖
   evaluation/coaching，于是永远只显示第一阶段。

## 修复

### 后端（app/api/v1/interviews.py `submit_answer`）

- 把 `ainvoke` 改为 `astream(..., stream_mode="updates")`，按节点完成顺序
  逐个发布事件：
  - `analyze_answer` → `analysis.completed`
  - `score_answer` → `scoring.completed`
  - `update_evidence` → `evidence.updated`（新增事件）
  - `generate_coaching` → `coaching.ready`
  - `generate_question` → `question.ready`
  - `generate_report` → `interview.finished` + `report.ready`
- 流结束后用 `aget_state(config)` 取完整最终状态，用于落库
  （answer / next question / report）与 `turn_count` / `finished` 回填。

### 前端

- `event-schema.ts`：`InterviewRuntimeState` 增加 `latestAnalysis` 与
  `evidenceUpdated`。
- `event-reducer.ts`：
  - `analysis.completed` 设置 `latestAnalysis`；
  - 新增 `evidence.updated` 分支置 `evidenceUpdated = true`；
  - `question.ready` 一并清空 `latestAnalysis` / `evidenceUpdated`。
- `interview-room-page.tsx`：
  - `AnalysisProgress` 新增 `hasAnalysis` / `hasEvidence` 两个 prop，
    四步依次对应 理解回答 / 多维评分 / 证据核验 / 预期回答，
    不再把第一步写死为 `done`。

## 验证

- 后端：`pytest tests/ -q` → 621 passed
- 前端：`pnpm type-check`、`pnpm lint`（0 errors）、`pnpm build` 通过
- 流式节点顺序实测：`wait_for_answer → analyze_answer → score_answer →
  update_evidence → generate_coaching → decide_next → generate_question`
