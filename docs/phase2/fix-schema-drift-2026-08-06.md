# 修复：模型 ↔ 迁移 schema 漂移对齐

**日期**: 2026-08-06
**状态**: ✅ 完成

---

## 背景

Codex 审查（第二轮，聚焦 schema audit）确认 `app/persistence/models.py` 与 Alembic 迁移存在多处列不一致。审查已证实其中三处为真实漂移，本任务将它们对齐。

## 修复的漂移

### 1. `interview_questions` — model 与 迁移/代码 不一致（CRITICAL）

- **迁移** `9f27a983fe62_initial_schema.py`：创建了 `data` JSON 列。
- **生产代码** `app/api/v1/interviews.py`（第 478、748 行）：`InterviewQuestion(..., data=current_q)` 写入 `data`，并在读取时大量使用 `question.data`（含 topic_id/claim_id/verification_point_id/depth）。
- **Model（错误）**：原声明 `question_text: Mapped[str]`，与迁移和代码都不符——生产 PG 上该列根本不存在，任何 `InterviewQuestion` 查询都会失败。

**修复**：`InterviewQuestion.question_text` → `data: Mapped[dict]`（JSON），与迁移和生产代码对齐。图状态层的 Pydantic schema（`app/interview/schemas.py`）保留 `question_text` 不受影响。

### 2. `evidence` — 删除 model 独有、未使用的列

- Model 原有 `strength`、`extraction_prompt_version` 两列，迁移 `ff8290d90189` 从未创建，且生产代码未使用（只有 `VerificationPoint.strength` 被使用）。

**修复**：从 `Evidence` 删除这两列。

### 3. `contradictions` — 删除 model 独有、未使用的列

- Model 原有 `answer_id` 列，迁移从未创建，生产代码构造 `Contradiction` 从不传 `answer_id`（仅 domain 层 `conflicting_answers` 使用）。

**修复**：从 `Contradiction` 删除 `answer_id` 列。

## 关联修改

- `tests/test_data_deletion.py`：`InterviewQuestion(question_text=...)` → `data={"question_text": ...}`。

## 验证

- `test_interview.py` / `test_interview_nodes.py` / `test_evidence_models.py` / `test_evidence_api.py` / `test_evidence_integration.py` / `test_data_deletion.py` / `test_evidence_state_machine.py` → **93 passed**。
- 完整后端套件回归运行中。

## 说明

- `resume_sources.user_id` / `interviews.user_id`：模型声明 NOT NULL，迁移为 nullable（`auth_m2_6_v1` 备注后续再收紧）。所有写入路径都设置 `user_id`，实际不产生问题，暂不强行收紧。
- 由于 model 已与迁移对齐（迁移本就含 `data`、不含 `strength`/`extraction_prompt_version`/`answer_id`），**无需新增迁移**。
