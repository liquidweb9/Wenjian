# 修复：报告/分析中文化（prompt 版本化）+ 报告未答题排除 + border 警告

**日期**: 2026-08-07
**状态**: ✅ 完成

---

## 1. 报告与每题分析为什么是英文 → 已改为中文

### 根因
4 个系统 prompt 全部是英文写的，LLM 会跟随 prompt 语言输出：
- `ANALYZER_PROMPT`（`app/interview/nodes/analyze_answer.py`）
- `SCORER_PROMPT`（`app/interview/nodes/score_answer.py`）
- `COACHING_PROMPT`（`app/interview/nodes/generate_coaching.py`）
- `REPORT_PROMPT`（`app/interview/nodes/generate_report.py`）

### 修复（按用户要求：英文记上一版、中文作当前版）
- 4 个常量改为简体中文（保留全部评分规则、维度权重、结构化字段契约不变；JSON 字段名保持英文，仅自然语言内容变中文）。
- 新增 `app/evals/prompts/interview_prompts_v2.json`：英文为 **version 1**（上一版）、中文为 **version 2**（当前版），覆盖 `answer_analysis` / `answer_scoring` / `coaching` / `report_generation` 四个 task。
- `app/main.py` lifespan 启动时调用 `load_prompts_from_file` 幂等注册 8 条版本记录（注册失败仅告警、不阻塞启动）。没有任何测试走 lifespan/TestClient，因此对测试无副作用。

### 验证
- 种子 JSON 合法；v2 中文与 4 个常量逐字节一致。
- `ruff` 通过；`app.main` 导入 OK；全套 599 passed。

> 说明：当前运行中的后端需重启后，新中文 prompt 与启动播种才生效（当前 uvicorn 无 `--reload`）。

## 2. 提前结束时未回答的问题进入报告

### 根因
`_build_report_context` 对 `[END OF INTERVIEW]` 的答案直接 `continue`（Q&A 上下文**不含**未答题），但 `_build_summary` 里 `asked_count = len(state["questions"])` **包含**屏幕上那道未答题，导致报告显示「已提问 N / 已答 N-1」，LLM 据此在 report_text 中写出「问了 N 只答了 N-1」。

### 修复（用户选择：不计入未答题）
`generate_report.py::_build_summary` 改为 `asked_count = answered_count`，提前结束时未回答的当前题从计数中完全排除（已问 == 已答）。同步更新 `REPORT_PROMPT` 中文版措辞（保留「`[END OF INTERVIEW]` 不计分」等规则，删除已无意义的「区分已问/已答」）。

### 验证
- 更新 `tests/test_report.py::test_fake_finish_answer_is_excluded_from_structured_questions` 断言（`Questions Asked: 2` → `1`），全套 599 passed。

## 3. React 警告：borderColor 与 border 简写混用

### 根因
`training-plan-page.tsx` 两处把 `border` 简写与非简写 `borderColor` 混用，切换状态时 React 19 移除 `borderColor` 而 `border` 仍在 → dev 警告：
- 筛选 tab：`{...styles.filterTab, ...(active ? styles.filterTabActive : {})}`，`filterTabActive.borderColor` 与 `filterTab.border` 共存。
- 任务卡片：`.app-surface`（CSS 的 `border` 简写）上叠加 inline `borderColor: isDone ? ... : undefined`。

### 修复
按 React 建议全部改用 `border` 简写：
- `filterTabActive`：`borderColor: "#0d1b2a"` → `border: "1px solid #0d1b2a"`。
- 任务卡片：`borderColor: isDone ? ... : undefined` → `border: isDone ? "1px solid rgba(22,163,74,0.35)" : undefined`。

### 验证
- `pnpm type-check` 通过（0 error）。
