# Phase 2.4: Ability Profile 页面完成

**日期**: 2026-08-05  
**状态**: ✅ 完成  
**任务**: Task #27 — 跨场次能力档案

---

## 目标

将已完成面试的报告聚合为「跨场次能力档案」：同一简历在多次面试中的能力评分、稳定性与迁移验证情况。后端从持久化的面试报告中派生聚合器可用的 observation，前端提供总览 + 单能力卡片展示。

---

## 实现内容

### 1. 后端 API (`app/api/v1/abilities.py`)

**`GET /api/v1/abilities/profile/{resume_id}`**

- 受 `get_current_user` 保护；简历不存在或不属于当前用户 → `404`（不泄露存在性）
- 查询该简历下所有已完成面试报告（按时间升序）
- 对每份报告的每个 `ability_scores` 维度派生一条 observation，交给 `AbilityAggregator.aggregate_observations()` 聚合
- 返回 `{ resume_id, total_interviews, competencies: [{ competency_code, profile, history }] }`
- `total_interviews` 只统计至少产生一条 observation 的报告

**`_build_observation(report_data, competency, created_at)`**
- 从报告的 `ability_scores` / `question_details` / `claim_statuses` 构造聚合器兼容的 observation
- 报告尚未持久化 `question_form`（M2.4 多形式接线未落地），用 7 级深度模型派生角度标签；**深度 7 映射为 `evolution` 而非 `counterfactual`**，避免仅凭深度误判迁移能力

**`_evidence_metrics(claim_statuses)`**
- 逐条 claim 独立识别格式：带 `verified_points` 数组的按点统计；字符串 / 无点 dict 按 legacy 模式（每条 claim 计 1 点，状态为 VERIFIED 才计已验证）
- **支持点格式与 legacy 格式混合**在同一报告中
- `VERIFIED` 仅当「所有已处理点全部已验证」（`verified_count == total_points`），部分验证不算 VERIFIED

**`_unresolved_contradictions(report_data)`**
- 从报告自身 `contradictions`（state 格式，`resolved` 布尔默认 False）统计未解决矛盾数
- 报告数据无法把矛盾归属到某个评分维度，因此矛盾数为**报告级**而非按能力归属——避免了之前按 `VerificationPoint.competency_code` 关联的跨分类法错配

### 2. 前端类型 (`lib/types/ability-profile.ts`)
- `StabilityLevel` / `TransferStatus` / `ScoreTrend`
- `StabilityFactors` / `CompetencyProfile` / `CompetencySummary` / `AbilityProfileResult`

### 3. API 层 + Hook (`features/ability-profile/api`, `hooks`)
- `abilityProfileApi.getProfile(resumeId)` → `GET /abilities/profile/{resumeId}`
- `useAbilityProfile(resumeId)` TanStack Query Hook（`resumeId` 为空时禁用）

### 4. 页面 (`features/ability-profile/pages/ability-profile-page.tsx`)
- **SummaryHeader**: 总面试数 / 能力维度数 / 平均能力分 / 高稳定性数 / 已测迁移数
- **CompetencyCard**（每能力一张）:
  - 稳定性徽章（高/中/低）
  - 平均得分、得分趋势（↗/→/↘）、迁移状态、问题形式数
  - 历次得分柱状图（按面试）
  - 稳定性因子条（跨场次数 / 形式多样性 / 分数一致性 / 证据强度）
  - 问题形式 chips + 待补强 gaps
- 加载 / 错误（含重试）/ 空状态

### 5. 路由与入口
- `app/router.tsx`: 新增 `/app/resumes/:resumeId/ability-profile`（lazy 加载）
- `resume-claims-page.tsx`: 新增「能力档案」按钮跳转

### 6. 测试 (`tests/test_ability_profile_api.py`) — 19 个用例
- 端点：404（不存在 / 他人简历）、空档案、聚合成功
- `_evidence_metrics`：点聚合、legacy 回退、混合格式、纯 partial 不判 VERIFIED、已验证+partial → PARTIALLY_SUPPORTED
- `_build_observation`：典型报告、显式 question_form 优先、深度 7 不产生 counterfactual、缺维度返回 None、无点 → UNVERIFIED、报告级矛盾数（跳过已解决）
- `_unresolved_contradictions`：只计未解决 / 缺数据返回 0

---

## 关键设计决策

1. **不引入跨分类法关联**：`ability_scores` 是评分维度（technical_correctness 等），而 `VerificationPoint.competency_code` 是岗位能力目录编码，二者不会匹配。因此矛盾数取报告级，避免错误归属。
2. **深度 7 → evolution**：7 级深度模型中没有 counterfactual 标签，若直接标 counterfactual 会误判迁移能力，故映射为 evolution。
3. **混合格式支持**：历史报告可能是纯字符串状态，新报告带 verified/partial/missing 数组，逐条判断保证两者共存时计数正确。

---

## 文件清单

### 新增
```
app/api/v1/abilities.py                      # 🆕 能力档案 API
frontend-react/src/features/ability-profile/
├── api/ability-profile-api.ts               # 🆕 API 层
├── hooks/use-ability-profile.ts             # 🆕 Query hook
└── pages/ability-profile-page.tsx           # 🆕 能力档案页面
frontend-react/src/lib/types/ability-profile.ts  # 🆕 类型定义
tests/test_ability_profile_api.py            # 🆕 后端测试
```

### 修改
```
app/main.py                                  # ✏️ 注册 abilities 路由
frontend-react/src/lib/query-keys.ts         # ✏️ abilities.profile 查询键
frontend-react/src/app/router.tsx            # ✏️ 新增路由
frontend-react/src/features/resumes/pages/resume-claims-page.tsx  # ✏️ 能力档案入口
```

---

## 验证

```bash
✅ python -m pytest tests/test_ability_profile_api.py -v   # 19 passed
✅ python -m ruff check app/api/v1/abilities.py tests/test_ability_profile_api.py
✅ cd frontend-react && pnpm type-check                    # 无错误
```

### 手动测试检查清单
- [ ] 未登录访问 `/app/resumes/:id/ability-profile` → 重定向 `/login`
- [ ] 访问他人简历的档案 → 404
- [ ] 无报告的简历 → 「暂无能力档案」空状态
- [ ] 有报告的简历 → 显示总览统计 + 每能力卡片
- [ ] 稳定性徽章 / 趋势 / 迁移状态正确渲染
- [ ] 错误状态点击「重新加载」可重试

---

## 下一步

- [ ] **Task #28**: Answer Diff 组件（同题重答对比）
- [ ] **Task #30**: Training Plan 页面（训练计划管理）

---

**创建时间**: 2026-08-05  
**实施者**: Claude Code
