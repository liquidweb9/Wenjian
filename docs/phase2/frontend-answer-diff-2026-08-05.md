# Phase 2.4: Answer Diff 组件完成

**日期**: 2026-08-05  
**状态**: ✅ 完成  
**任务**: Task #28 — 同题重答对比

---

## 目标

当同一道题被多次作答时，前端需要展示版本对比：高亮新增/删除内容、标识新增证据、展示评分与实质变化。本任务交付了可复用的「作答版本对比」组件、后端版本查询接口，并接入面试房间的历史问答查看。

---

## 实现内容

### 1. 后端接口 (`app/api/v1/answer_diff.py`)

**`GET /api/v1/interviews/{interview_id}/questions/{question_id}/versions`**

- 受 `get_current_user` 保护；面试不存在或不属于当前用户 → `404`
- 读取该问题下的全部 `InterviewAnswer`（按创建时间升序）
- 相邻版本之间用 `AnswerDiffer.compute_diff()` 实时计算 diff
- 每个版本返回：`version_number` / `answer_id` / `answer_text` / `created_at` / `score` / `diff`
  - `score` 从答案的 `evaluation` 用 `calculate_weighted_score` 加权得出（无评估则为 `null`）
  - `diff` 仅 v2+ 存在，含 `added_tokens`、`removed_tokens`、`new_evidence`、`coaching_repetition`、`is_substantive_change`、`change_ratio`
- 在 `app/main.py` 注册

### 2. 前端类型 (`lib/types/answer-diff.ts`)
- `AnswerDiffSummary` / `AnswerVersion` / `AnswerVersionResult`

### 3. API 层 + Hook (`features/answer-diff/`)
- `answerDiffApi.getVersions(interviewId, questionId)`
- `useAnswerVersions(interviewId, questionId)` TanStack Query Hook（空参禁用）
- `query-keys.ts` 新增 `answerDiff.versions(interviewId, questionId)`

### 4. 组件 (`features/answer-diff/components/answer-diff-viewer.tsx`)
- **版本 Tab 选择**：v1 / v2 / …，可切换查看任一版本
- **Diff 高亮**：基于 LCS 的 token 级对比，中文按字、英文按词粒度；新增内容绿底、删除内容红底删除线
- **新增/删除证据标识**：`new_evidence` → 「新增证据」，`is_substantive_change` → 「实质改进」，`coaching_repetition` → 「疑似复述反馈」
- **评分变化展示**：相邻版本均有分时显示 `old → new` 及差值箭头；否则显示 diff 派生的变化比例
- **变化比例**：展示 `change_ratio` 百分比

### 5. 集成（面试房间）
- 面试房间 `HistoryDetail` 查看历史问答时，若某题存在 ≥2 个版本，自动渲染「版本对比」面板
- 单版本题目仍走原有「你的回答」展示，不额外渲染

### 6. 测试 (`tests/test_answer_diff_api.py`) — 7 个用例
- 端点：404（不存在 / 他人面试）、无回答空版本、单版本无 diff、双版本有 diff（含新增证据与变化比例）
- `_answer_score`：从 evaluation 提取加权分；无 evaluation / 非 dict → `null`

---

## 关键设计决策

1. **不额外写库**：版本从持久化的 `InterviewAnswer` 行派生，相邻版本实时计算 diff，避免在面试热路径上增加写操作与事务风险。
2. **前端做 token 级 diff**：后端只返回 token 集合与统计，行内高亮由组件用 LCS 算法在客户端完成，保证展示粒度（中文按字）。
3. **评分可选**：`InterviewAnswer` 的评价列在运行时可能缺失，评分允许 `null`，组件退化显示「无逐版本数据」。

---

## 修复的既有缺陷

**`InterviewAnswer` 模型缺少 `analysis` / `evaluation` 列**：数据库迁移（`9f27a983fe62_initial_schema.py`）已创建这两列，但 SQLAlchemy 模型未映射，导致 `submit_answer` 在每次保存回答时以 `TypeError` 崩溃（`'analysis' is an invalid keyword argument`）。已在 `app/persistence/models.py` 补齐这两列，模型与库结构对齐。此修复同时让 `get_interview` 读取 `answer.analysis` / `answer.evaluation` 不再报错。

---

## 文件清单

### 新增
```
app/api/v1/answer_diff.py                          # 🆕 版本查询接口
frontend-react/src/features/answer-diff/
├── api/answer-diff-api.ts                         # 🆕 API 层
├── hooks/use-answer-diff.ts                       # 🆕 Query hook
└── components/answer-diff-viewer.tsx              # 🆕 版本对比组件
frontend-react/src/lib/types/answer-diff.ts        # 🆕 类型定义
tests/test_answer_diff_api.py                      # 🆕 后端测试
```

### 修改
```
app/main.py                                        # ✏️ 注册 answer_diff 路由
app/persistence/models.py                          # ✏️ 补齐 analysis/evaluation 列
frontend-react/src/lib/query-keys.ts               # ✏️ answerDiff.versions 查询键
frontend-react/src/features/interviews/pages/interview-room-page.tsx  # ✏️ HistoryDetail 集成
```

---

## 验证

```bash
✅ python -m pytest tests/test_answer_diff_api.py -v      # 7 passed
✅ python -m pytest tests/test_answer_diff.py tests/test_interview.py tests/test_interview_nodes.py  # 61 passed
✅ python -m ruff check app/api/v1/answer_diff.py app/persistence/models.py tests/test_answer_diff_api.py
✅ cd frontend-react && pnpm type-check                  # 无错误
```

### 手动测试检查清单
- [ ] 未登录访问版本接口 → 重定向 / 401
- [ ] 访问他人面试的版本 → 404
- [ ] 面试房间历史问答中，单版本题目不显示「版本对比」
- [ ] 双版本题目显示 v1/v2 Tab、diff 高亮、证据标识与评分变化
- [ ] 切换版本 Tab 显示对应回答全文

---

## 下一步

- [ ] **Task #30**: Training Plan 页面（训练计划管理 + 复验）

---

**创建时间**: 2026-08-05  
**实施者**: Claude Code
