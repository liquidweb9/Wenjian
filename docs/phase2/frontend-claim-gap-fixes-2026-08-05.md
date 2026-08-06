# Claim Gap / Job Target 修复完成

**日期**: 2026-08-05  
**状态**: ✅ 完成  
**任务**: Task #36-#39 — 修复 Codex 审查发现的 claim-gap 与 job-target 前后端问题

---

## 背景

Codex 代码审查（前端完整性审计）发现 Claim Gap 前端 mutation 提交的端点不存在；进一步验证发现整个 job-targets + claim-gap 链路存在系统性前后端契约不一致，且后端多个端点 500。本任务集中修复。

---

## 已修复的问题

### 1. 根因：`JobTarget.requirements` relationship 缺失 (`app/persistence/models.py`)
- `selectinload(JobTarget.requirements)` 与 `job_target.requirements` 在多个端点使用，但模型从未定义该关系 → **所有 job-targets 端点 + claim-gap 端点 500**（`AttributeError: no attribute 'requirements'`）
- 修复：`JobTarget.requirements = relationship(back_populates="job_target", cascade="all, delete-orphan")` + `JobRequirement.job_target` 反向引用

### 2. `JobTarget.description` 列缺失
- API 模型（`JobTargetCreate`/`JobTargetResponse`）与前端类型都使用 `description`，但 schema 与模型都无此列 → create 报 `TypeError: 'description' is an invalid keyword argument`
- 修复：模型加列 + 新增迁移 `migrations/versions/add_job_targets_description.py`（nullable，兼容既有行）

### 3. Claim Gap 前端端点路径错误 (`frontend-react/src/features/claim-gap/api/claim-gap-api.ts`)
- 前端调用 `POST /claim-gap/analyze`、`GET /claim-gap/{resumeId}/{jobTargetId}` → 均 404
- 后端实际：`POST /claim-gap`、`GET /claim-gap/resume/{resume_id}/job-target/{job_target_id}`
- 修复：前端路径对齐后端

### 4. Claim Gap 前后端契约完全不一致
- 前端 `GapAnalysisResult`（`overall_coverage`/`summary`/`gaps[].priority_score`/`recommendation` 等）与后端 `ClaimGapResponse`（`coverage_stats`/`gaps[].priority`/`explanation` 等）形状完全不同 → 页面渲染崩
- 修复：以测试完善的后端为基准，重写前端
  - `src/lib/types/claim-gap.ts` — `GapType` 对齐后端 enum（`WEAK_EVIDENCE_CLAIM`、`IRRELEVANT_CLAIM`），响应类型对齐 `ClaimGapResponse`
  - `coverage-overview.tsx` / `requirement-coverage.tsx` / `gap-list.tsx` / `gap-badge.tsx` — 消费 `coverage_stats` 与后端 gap 字段
  - `reports/components/JDCoverageSection.tsx` — 同步对齐
  - 删除死代码 `claim-gap/api/claim-gap.ts`

### 5. `ResumeClaim.text` 不存在 (`app/api/v1/claim_gap.py`)
- 声明文本存在 `claim.data["claim_text"]`，端点却用 `claim.text` → claim-gap 仍 500
- 修复：`claim.data.get("claim_text", "")`

### 6. `parse-jd` 路由与 gateway 调用不匹配
- 路由：前端 `POST /job-targets/parse-jd` vs 后端 `POST /job-targets/{job_target_id}/parse-jd`（参数未使用）→ 404；改为 `POST /job-targets/parse-jd`
- `jd_parser.py` 以 `prompt=` 调用 `generate_structured`，而真实 `AgnesGateway` 签名是 `system_prompt` + `user_payload` → 400；修复 JDParser 调用 + Protocol + MockLLMGateway

### 7. 重复 DELETE 路由冲突
- 我新增的 `DELETE /job-targets/{id}` 与 `auth.py` 已有的带所有权校验的删除端点冲突（auth 路由先注册，401）
- 修复：移除重复 DELETE，复用 auth.py 的端点（前端带 token 即可）

---

## 验证

```bash
✅ pytest tests/test_claim_gap_analyzer.py tests/test_claim_mapper.py tests/test_job_target_templates.py -q   # 53 passed
✅ pytest tests/test_jd_parser.py -q                                                                         # 15 passed
✅ pytest tests/ -q --ignore=tests/test_evidence_api.py    # 545 passed（失败均为既有异步/测试数据问题，与本次无关）
✅ ruff check app/api/v1/job_targets.py app/api/v1/claim_gap.py app/persistence/models.py app/job_target/jd_parser.py
✅ cd frontend-react && pnpm type-check                # 0 errors
✅ cd frontend-react && pnpm lint                      # 0 errors
✅ pnpm test:e2e                                        # 17 passed / 5 skipped / 0 failed
```

### 端点验证（curl，运行中后端）
- `GET /api/v1/job-targets` → 200（原 500）
- `POST /api/v1/job-targets` → 201，返回 requirements
- `GET /api/v1/job-targets/{id}` → 200
- `PATCH /api/v1/job-targets/{id}` → 200
- `DELETE /api/v1/job-targets/{id}` → 401（走 auth.py 路由，前端带 token 即可）
- `POST /api/v1/job-targets/parse-jd` → 200（真实 LLM 提取成功）
- `POST /api/v1/claim-gap` → 200，返回 coverage_stats/gaps/interview_plan
- `GET /api/v1/claim-gap/resume/{r}/job-target/{j}` → 200（原 500）

---

## 遗留说明

- 完整套件的既有失败（test_e2e_flows async 基础设施、test_evidence_*、test_data_deletion 的 sqlite thread_id 约束）与本次改动无关。

---

# 第二轮：Codex 复审发现的 6 项问题修复

**日期**: 2026-08-05（同日）

Codex 复审（聚焦本次修复）确认 5 项契约修复全部正确（INFO），另发现 2 个 BLOCKER + 4 个 SHOULD-FIX，均已修复：

1. **BLOCKER — job-targets 无认证/所有权** (`app/api/v1/job_targets.py`)
   - create/update/get/list 全部加 `get_current_user`
   - create 设置 `user_id=user.user_id`
   - get/update 校验 `job_target.user_id == user.user_id`（他人 → 404）
   - list 只返回当前用户的 targets
2. **BLOCKER — claim-gap 无认证/所有权** (`app/api/v1/claim_gap.py`)
   - POST/GET 加 `get_current_user`
   - 校验 resume 归属（`ResumeSource.user_id`）与 job_target 归属
3. **SHOULD-FIX — PATCH 非空列可被置 null** (`job_targets.py:46-56`)
   - `JobTargetUpdate` 加 `model_validator`：`title/level/interview_round/source` 显式 null → 400
4. **SHOULD-FIX — PATCH 忽略 requirements**（前端详情页提交 `requirements`，后端未定义）
   - `JobTargetUpdate` 加 `requirements: list[RequirementCreate] | None`，update 端点替换 requirements（`clear()` + 重新 append，依赖 delete-orphan cascade）
   - 修复 `model_dump()` 将 requirements 序列化为 dict 导致的 `'dict' object has no attribute 'competency_code'`
5. **SHOULD-FIX — 账号删除 FK 违规** (`app/core/data_deletion.py:100-103`)
   - bulk `delete(JobTarget)` 绕过 ORM cascade，FK 无 DB 级 CASCADE → 新增迁移 `add_job_requirements_cascade.py` 给 `job_requirements_job_target_id_fkey` 加 `ON DELETE CASCADE`
6. **SHOULD-FIX — UNCOVERED 双重渲染** (`requirement-coverage.tsx:17-26`)
   - `UNCOVERED_REQUIREMENT` gap 不再加入 `requirementMap`（单独渲染）

## 第二轮验证

```bash
✅ pytest tests/test_claim_gap_analyzer.py tests/test_claim_mapper.py tests/test_job_target_templates.py tests/test_jd_parser.py -q   # 68 passed
✅ ruff check app/api/v1/job_targets.py app/api/v1/claim_gap.py        # clean
✅ cd frontend-react && pnpm type-check                                # 0 errors
✅ cd frontend-react && pnpm lint                                      # 0 errors
✅ pnpm test:e2e                                                        # 17 passed / 5 skipped / 0 failed
```

### 认证流程端点验证（curl + 真实 JWT）
- `GET /job-targets` 无 token → **401**；带 token → **200**（只含本人 targets）
- `POST /job-targets` 带 token → **201**（user_id 已设置）
- `GET /job-targets/{id}` 带 token → **200**；他人 → 404
- `PATCH /job-targets/{id}` 带 token（title+requirements 替换）→ **200**（requirements 更新生效）
- `DELETE /job-targets/{id}` 带 token → **204**（auth.py 所有权删除）
- `GET /claim-gap/...` 无 token → **401**；带 token + 非本人 resume → **404**
- 迁移 `add_job_requirements_cascade` 已应用（DB FK 带 CASCADE）

---

# 第三轮：Codex 复审（确认）发现的遗留问题修复

**日期**: 2026-08-06

Codex 确认审查确认第二轮 6 项修复全部正确，另发现 4 项 SHOULD-FIX + 1 项 NIT，均已处理：

1. **SHOULD-FIX — requirement description 可为 None 但 DB NOT NULL** (`job_targets.py:23-30`)
   - `RequirementCreate.description` 可选，`job_requirements.description` NOT NULL → 缺省时 DB 失败
   - 修复：create/update 构造 JobRequirement 时 `description=req_data.description or ""`
2. **SHOULD-FIX — interviews 缺 `job_target_id` 列** (`models.py:121` / DB schema)
   - 模型声明 `Interview.job_target_id`（创建面试时写入），DB 无此列 → 带 job_target 的面试创建会失败；且删除被引用的目标无 FK 保护
   - 修复：迁移 `add_job_target_to_interviews.py` 加列 + FK `ON DELETE SET NULL` + 索引（对应 `migrations/add_job_target_to_interviews.sql` 的意图）
3. **SHOULD-FIX — auth-store rehydration bug** (`stores/auth-store.ts:49-59`)
   - `onRehydrateStorage` 直接改 `state.isAuthenticated` 不走 `set()`，且自引用 store（`create()` 完成前触发 → TDZ ReferenceError）→ 刷新后会话停留在未认证态
   - 修复：改用 persist 的 `merge` 选项在 hydration 时派生 `isAuthenticated`（`Boolean(p.token)`）
4. **SHOULD-FIX — DELETE /job-targets/{id} 误报 405**
   - Codex 只看了 `job_targets.py`（无 DELETE 路由），实际由 `auth.py` 的 DELETE 端点服务（带 token 返回 204，已验证）；无需改动
5. **NIT — 死目录 `features/job-targets/`**（复数版）
   - 未被路由引用，调用旧 `/{jobTargetId}/parse-jd` 路径；已删除

## 第三轮验证

```bash
✅ ruff check app/api/v1/job_targets.py app/api/v1/claim_gap.py   # clean
✅ pytest tests/test_claim_gap_analyzer.py tests/test_claim_mapper.py tests/test_job_target_templates.py tests/test_jd_parser.py   # 68 passed
✅ cd frontend-react && pnpm type-check / pnpm lint               # 0 errors
✅ pnpm test:e2e                                                    # 17 passed / 5 skipped / 0 failed
```

### 端点验证（curl + JWT）
- 无 description 的 create → **201**（req description 默认 ""）
- `GET /interviews`（新增 job_target_id 列后）→ **200**
- E2E 在 auth-store merge 修复后恢复全绿

---

**创建时间**: 2026-08-05（三轮同日续）  
**实施者**: Claude Code
