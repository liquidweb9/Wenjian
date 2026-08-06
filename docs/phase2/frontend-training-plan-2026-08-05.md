# Phase 2.4: Training Plan 页面完成

**日期**: 2026-08-05  
**状态**: ✅ 完成  
**任务**: Task #30 — 训练计划管理

---

## 目标

根据简历能力档案中的证据缺口与能力短板，生成可执行的训练任务；提供任务列表、类型标签、完成标准展示与「启动复验」入口，帮助用户针对性补强后回到面试验证。

---

## 实现内容

### 1. 后端接口 (`app/api/v1/training_plans.py`)

**`GET /api/v1/training-plans?resume_id=...`**
- 受 `get_current_user` 保护，只返回当前用户的任务
- 指定 `resume_id` 时校验简历归属（他人 → `404`）
- 按 `priority` 降序、`created_at` 升序返回

**`POST /api/v1/training-plans/{resume_id}/generate`**
- 校验简历归属
- 复用能力档案的 observation 构建（见下），对每个维度聚合 profile 后调用 `TrainingPlanGenerator.generate_tasks`
- 替换该简历现有的 `PENDING` / `IN_PROGRESS` 任务，保留已完成/已放弃的历史
- `priority`（生成器为 0-1 浮点）转换为 0-100 整数存储

**`PATCH /api/v1/training-plans/{task_id}`**
- 校验状态合法（PENDING/IN_PROGRESS/COMPLETED/DISMISSED）与任务归属
- 置为 COMPLETED 时写 `completed_at`

### 2. 复用能力档案构建逻辑（`app/api/v1/abilities.py` 重构）
- 提取 `_load_report_rows(session, resume_id, user_id)` 与 `_observations_by_competency(rows)` 为模块级函数
- 能力档案接口与训练计划生成共用同一份 observation 派生逻辑，保证两者口径一致

### 3. 前端类型 (`lib/types/training-plan.ts`)
- `TrainingTaskStatus` / `TrainingTask` / `TrainingTaskResult`
- `completion_criteria` 兼容 dict（新生成）与数组（legacy）

### 4. API 层 + Hook (`features/training-plan/`)
- `trainingPlanApi.list/generate/updateStatus`
- `useTrainingPlan`（列表查询）、`useGenerateTrainingPlan`、`useUpdateTrainingTask`（成功后失效列表查询）
- `query-keys.ts` 新增 `trainingPlan.list(resumeId)`

### 5. 页面 (`features/training-plan/pages/training-plan-page.tsx`)
- **总览统计**：待开始 / 进行中 / 已完成 / 总任务数
- **「生成训练计划」**：一键从能力档案生成任务
- **状态筛选 Tab**：全部 / 待开始 / 进行中 / 已完成 / 已放弃
- **任务卡片**：
  - 任务类型标签（补充证据 / 概念复习 / 深度提升 / 矛盾澄清 / 形式多样化 / 迁移练习）
  - 状态徽章 + 优先级
  - 描述（保留换行）
  - 完成标准展示（dict 键值对带中文标签，或 legacy 数组列表）
  - 状态操作：开始训练 / 标记完成 / 放弃 / 恢复
- **启动复验面试**：跳转 `/app/interviews/new?resume_id={resumeId}`（创建页已支持该查询参数预选简历），复用现有创建流程

### 6. 路由与入口
- 路由：`/app/resumes/:resumeId/training-plan`（lazy 加载）
- `resume-claims-page.tsx` 新增「训练计划」按钮（与「能力档案」并列）

### 7. 测试 (`tests/test_training_plan_api.py`) — 7 个用例
- `list_tasks`：他人简历 404、返回排序后的任务
- `generate_tasks`：他人简历 404、从报告生成任务
- `update_task_status`：非法状态 400、他人任务 404、更新成功

---

## 关键设计决策

1. **复用 observation 构建**：生成训练计划直接复用能力档案的 report→observation 逻辑，保证「档案里的缺口」与「计划里的任务」来自同一口径。
2. **生成替换待办不删历史**：重新生成只清空 PENDING/IN_PROGRESS，保留已完成/已放弃，避免丢失训练痕迹。
3. **启动复验走现有创建流程**：跳转到 `?resume_id=` 预选，让用户顺带选择岗位目标等复验配置，而不是在训练计划接口里再造一套创建逻辑。

---

## 文件清单

### 新增
```
app/api/v1/training_plans.py                       # 🆕 训练计划接口
frontend-react/src/features/training-plan/
├── api/training-plan-api.ts                       # 🆕 API 层
├── hooks/use-training-plan.ts                     # 🆕 Query / mutations
└── pages/training-plan-page.tsx                   # 🆕 训练计划页面
frontend-react/src/lib/types/training-plan.ts      # 🆕 类型定义
tests/test_training_plan_api.py                    # 🆕 后端测试
```

### 修改
```
app/api/v1/abilities.py                            # ✏️ 提取共享 observation 构建
app/main.py                                        # ✏️ 注册 training_plans 路由
frontend-react/src/lib/query-keys.ts               # ✏️ trainingPlan.list 查询键
frontend-react/src/app/router.tsx                  # ✏️ 新增训练计划路由
frontend-react/src/features/resumes/pages/resume-claims-page.tsx  # ✏️ 训练计划入口
```

---

## 验证

```bash
✅ python -m pytest tests/test_training_plan_api.py -v        # 7 passed
✅ python -m pytest tests/test_ability_profile_api.py tests/test_answer_diff_api.py tests/test_training_plan_api.py  # 33 passed
✅ python -m pytest tests/test_ability_aggregator.py tests/test_report.py -q   # 无回归
✅ python -m ruff check app/api/v1/training_plans.py app/api/v1/abilities.py tests/test_training_plan_api.py
✅ cd frontend-react && pnpm type-check                      # 无错误
```

> 注：`tests/test_evidence_api.py` 的 3 个失败为既有的证据接口问题，与本任务无关（早前已用 git stash 确认）。

### 手动测试检查清单
- [ ] 未登录访问 `/app/resumes/:id/training-plan` → 重定向 `/login`
- [ ] 无报告的简历 → 空状态，可「立即生成」
- [ ] 有报告的简历 → 点击「生成训练计划」后出现任务卡片
- [ ] 任务类型标签 / 完成标准正确渲染
- [ ] 开始训练 / 标记完成 / 放弃 / 恢复可用
- [ ] 状态筛选 Tab 生效
- [ ] 「启动复验面试」跳转到创建页并预选该简历

---

## 下一步

待办任务 #15（并发面试负载测试）仍 pending，非前端。

---

**创建时间**: 2026-08-05  
**实施者**: Claude Code
