# 修复：Q4 评分失败导致「评分数据仍在整理中」+ 评分 JSON 结构损坏

日期：2026-08-07

## 现象

Q4 答题后，「评分结果」面板一直显示「评分数据仍在整理中」，且「改进建议」
只有兜底文案（`coaching_from_evidence` 的通用评分依据说明）。

## 根因

1. 评分 LLM（`deepseek-v4-flash`，judge 档）偶发输出结构损坏的 JSON：
   `dimensions` 数组从第二个元素起丢弃对象开括号 `{` 与 `"dimension"`/`"score"`
   键，直接输出裸的 `}, "implementation_depth": 20, "max_score": 100, ...`。
2. `_parse_json` 只修复控制字符（`_escape_string_control_chars`），无法处理
   结构缺失 → 3 次重试全部同样失败（`llm_retry_parse`）→
   `score_answer_node` 走 `except` 分支写入空评价兜底
   （`dimensions: []`、`evaluation_confidence: 0.0`）。
3. 前端 `ScoreDisplay` 把「dimensions 为空」一律当作「还在整理中」，没有区分
   「仍在整理」与「评分失败」，于是错误地一直显示「评分数据仍在整理中」。
4. 复现验证：相同入参直调 8 次全部返回合法 JSON → 确认是偶发模型输出问题，
   而非必然 bug。

## 修复 A：JSON 结构修复（后端）

### 1. `app/llm/agnes_api.py` `_parse_json`

- 引入 `json-repair>=0.20.0` 依赖（已加入 `pyproject.toml`）。
- `_parse_json` 在控制字符修复仍失败后，追加 `repair_json()` 结构修复兜底
  （rebalance 数组元素缺失的 `{`），成功则解析返回；仍失败才抛异常。

### 2. `app/llm/agnes_api.py` / `app/llm/gateway.py` `generate_structured`

- 新增可选参数 `repair: Callable[[dict], dict] | None`，在 `_parse_json` 之后、
  `output_model.model_validate` 之前对解析结果做 schema 级修复。
- Protocol（`LLMGateway`）同步签名。

### 3. `app/interview/nodes/score_answer.py`

- 新增 `_repair_dimensions(parsed)`：把扁平化维度条目
  `{"implementation_depth": 20, "max_score": 100, ...}` 重写回 schema 形状
  `{"dimension": "implementation_depth", "score": 20, ...}`。
- `generate_structured(..., repair=_repair_dimensions)` 接入。

## 修复 B：前端区分「评分失败」（`interview-room-page.tsx`）

- 后端 `except` 兜底评价增加 `scoring_failed: True` 标记。
- `ScoreDisplay`：当 `evaluation.scoring_failed === true` 时显示明确的失败
  提示（「本次评分未能生成：模型返回的结果无法解析…」），不再显示
  「评分数据仍在整理中」；`dimensions` 为空且非失败时才显示「整理中」。

## 验证

- `pytest tests/ -q` → 626 passed
- `ruff check` 涉及文件 → All checks passed
- `pnpm type-check` → 0 errors；`pnpm lint` → 仅既有警告；`pnpm build` 通过
- 新增测试：
  - `TestJSONRepair::test_parse_json_repairs_missing_object_braces_in_array`
  - `TestDimensionRepair`（扁平化重写 / 正常条目不变 / 缺 key 容错）
- 端到端验证：对 Q4 同款畸形 JSON 依次 `repair_json` → `_repair_dimensions`
  → `AnswerEvaluation.model_validate`，成功还原全部维度分数。
