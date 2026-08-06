# 修复：主张提取结果全被丢弃（entry_id 不匹配）

**日期**: 2026-08-06
**状态**: ✅ 完成

---

## 问题报告

用户确认简历后，最新简历没有任何 ResumeClaim，画像页显示「当前还没有结构化主张证据」。且证据（evidence）为空。

## 根因

`app/resume/claim_extractor.py` 存在一个管线 bug，导致**每一份真实简历**的主张提取都会产出 0 条：

1. `app/resume/profile_builder.py:108` 给每条画像条目生成**随机 entry_id**（`new_id("entry")` → `entry_<12位hex>`）。
2. `ClaimExtractor._format_entries()` 格式化喂给 LLM 的条目文本时**不包含 entry_id**（只含 `[section] 标题 @ 组织` + bullets + 技术栈）。
3. LLM 返回的每条主张都要带 `entry_id`，但它看不到真实 id，只能自造。
4. `_limit_claims()` 用「`claim.entry_id` 必须在画像真实 entry_id 集合中」严格过滤 → **全部主张被丢弃 → 0 条**。

佐证：后端日志中该次提取 `output_tokens=15008`（LLM 实际输出了大量主张），但 `claims_extracted count=0`，说明是过滤环节丢光，而非 LLM 返回空。

## 修复

`app/resume/claim_extractor.py`：

- `_format_entries()`：条目文本加入 `id=<entry.entry_id>`，使 LLM 能看到并引用真实 id。
- `CLAIM_EXTRACTOR_PROMPT` 规则 5：明确要求每条主张复制源条目的 `id=` 值，且只引用 experience/project/research 区段。
- `_limit_claims()`：被丢弃的主张计数并记 `claims_dropped_bad_entry_id` 警告日志（kept/dropped/resume_id），便于将来发现 LLM 仍对不上 id 的情况。

## 测试

`tests/test_claim_extractor.py` 新增 2 个用例：
- `_format_entries` 输出包含 `id=`。
- `_limit_claims` 保留引用已知 entry_id 的主张、丢弃编造的 id。

原有 `test_claim_budget_excludes_education_and_limits_each_entry` 等用例继续通过。

## 验证

- `tests/test_claim_extractor.py` → 4 passed。
- 后端已重启；对用户最新简历重新执行 confirm/extract，主张已正常落库（见结果）。
