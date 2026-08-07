# 修复：回答处理链路（评分/改进建议缺失）与问题去重

**日期**: 2026-08-07
**状态**: ✅ 完成

---

## 背景

真实面试（`int_613a87c7e062`）中 Q1 回答提交后，前端评分区显示「评分数据仍在整理中」，改进建议只显示通用摘要。排查发现是 LLM 输出解析失败导致评分走 fallback，进而引发 coaching 基于空评分只出兜底文案。随后又发现 Q1/Q2 问题逐字重复，以及证据引擎调用签名不匹配等多处连锁 bug。

## 问题一：评分为空（LLM JSON 解析失败）

### 现象

- 日志：`scoring_failed error="Expecting ',' delimiter: line 21 column 27 (char 665)"`，三次重试均失败
- 数据库：Q1 evaluation 为 fallback（`dimensions: []`、`demonstrated_level: unknown`）

### 根因

`app/llm/agnes_api.py::_parse_json` 只用严格 `json.loads`，而评分 LLM（deepseek-v4-flash）在 JSON 字符串值里输出**未转义的控制字符**（原始换行/制表符），且常带 markdown fence、前后夹带 prose。任何一处即导致解析失败。

### 修复（`agnes_api.py`）

- **`_escape_string_control_chars()`**：逐字符扫描，将字符串字面量内的裸 `\n`/`\r`/`\t`/`\b`/`\f` 转义为 JSON 合法形式；结构空白不受影响
- **`_parse_json` 增强**：先剥 markdown fence → 提取首尾 `{...}` 片段（去掉前后 prose）→ 严格解析 → 失败后走控制字符修复再解析；仍失败才抛错走重试
- **LLM 调用日志增强**：`llm_call` 增加 `input_preview` / `output_preview`（`sanitize_for_log` 脱敏，各 800 字符）；`json_parse_failed` 增加 `raw_preview`（400 字符），失败时可直接看到损坏原文，便于定位

## 问题二：证据引擎调用签名不匹配（evidence 一直为空）

### 现象

`evidence_update_failed error="AgnesGateway.generate_structured() got an unexpected keyword argument 'messages'"`，导致 evidence/contradiction/transition 表永远为空。

### 根因

证据引擎（`app/evidence/span_extractor.py`、`contradiction_detector.py`）自带 `LLMGateway` Protocol，以 `messages=[...]` 方式调用；而 `AgnesGateway.generate_structured` 只接受 `system_prompt` + `user_payload`。两套协议不一致，证据引擎调用必然失败。

### 修复

- `generate_structured` 增加可选 `messages: list[dict] | None`，收到时直接透传（注入检测、schema 指令、token 日志仍生效），兼容两种调用风格
- `app/llm/gateway.py` 的 `LLMGateway` Protocol 同步补充 `messages` 参数

## 问题三：claim 验证点字段名错误（evidence 外键违约）

### 现象

签名修复后出现 `IntegrityError: evidence_verification_point_id_fkey`，`verification_points` 表中无对应 VP 记录。

### 根因

- claim 数据里验证点标识字段叫 **`point_id`**，而 `update_evidence_node::_get_vp_from_claim` 读的是 `verification_point_id` → 永远匹配不到 → VP 记录未创建 → 后续 evidence 插入违反外键
- 即使 VP 创建，`aspect` 取 `vp_dict.get("aspect")` 为 None，导致 span 提取（依赖 aspect 描述）返回 0 条，evidence 依然为空

### 修复（`update_evidence.py`）

- `_get_vp_from_claim`：兼容 `point_id` 与 `verification_point_id` 两种字段名
- 创建 VP 时 `aspect = vp_dict.get("aspect") or vp_dict.get("description") or ""`，用 claim 的 `description` 兜底

## 问题四：Q1/Q2 问题逐字重复

### 现象

Q2 与 Q1 `question_text` 完全一致（仅 depth 4→5），用户看到连续两题完全相同。

### 根因

`generate_question_node` 已把 Q1 文本放进 `previous_questions`（prompt 规则 8 "Never repeat"），但复现确认 LLM（deepseek-v4-flash）**仍输出逐字相同文本**——纯依赖 LLM 自觉不可靠。

### 修复（`generate_question.py`）：prompt 强化 + 代码层兜底

**Prompt 强化**
- 规则 8 明确 `previous_questions` 是 STRICT BLACKLIST，重复/改写/换措辞均视为失败，要求探询新角度（具体失败场景/权衡/边界/可量化结果）
- 新增规则 9：`force_new_angle` 为 true 时必须选一个具体新角度，并参考 `suggested_new_angles`

**代码层兜底（不依赖 LLM）**
- `_normalize_text` / `_similarity` / `_ngram_similarity`：归一化后做字符级 SequenceMatcher ratio + trigram Jaccard 双重相似度
- `_is_duplicate`：任一指标超阈值（0.65 / 0.5）即判重复
- `_suggest_angles`：根据已问内容排除已覆盖角度，提供候选新角度（故障/权衡/边界/扩展/回滚/监控）
- 生成循环：最多重试 2 次，重试时置 `force_new_angle=true` 并附候选角度；命中重复则记录 `question_duplicate_detected` 日志并重试
- 重试耗尽仍重复或 LLM 失败时，`_fallback_question` 生成确定性兜底问题，保证与历史不同

## 验证

- 单元测试：新增 `tests/test_llm.py::TestJSONRepair`（9 个）、`tests/test_question_dedup.py`（13 个）
- 端到端复现：真实 LLM 重现 Q1 评分 → 成功解析 6 维度；Q2 生成首次仍重复 → 触发去重 → 重试产出全新问题（`duplicate of Q1: False`）
- 全量回归：`pytest tests/` **621 passed**（原 599 + 新增 22）
- ruff：相关文件全部通过

## 关联文件

- `app/llm/agnes_api.py`：`_parse_json` 容错、`_escape_string_control_chars`、`generate_structured` 兼容 messages、LLM 日志增强
- `app/llm/gateway.py`：Protocol 同步
- `app/interview/nodes/update_evidence.py`：VP 字段名兼容、aspect 兜底
- `app/interview/nodes/generate_question.py`：prompt 强化 + 相似度去重 + 重试 + 兜底
- `tests/test_llm.py`、`tests/test_question_dedup.py`
- 数据修复脚本（临时）：重建 Q1 全链路（analyze → score → update_evidence → coaching → decide）并回写 DB
