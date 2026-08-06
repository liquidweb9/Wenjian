# 修复：创建面试前端超时（120s → 600s）

**日期**: 2026-08-07
**状态**: ✅ 完成

---

## 问题报告

用户点击「确认并开始面试」后提示 `timeout of 120000ms exceeded`。

## 根因

`POST /api/v1/interviews`（`app/api/v1/interviews.py:394`）**同步**执行 LangGraph 直到第一个问题生成（`build_plan` + `generate_question` 均为 LLM 调用）。在 LLM 延迟 2-3 分钟的环境下，单次创建耗时超过前端 axios 的全局 **120s 超时**（`api-client.ts`）。

**关键点**：后端实际**成功创建**了面试（日志 `interview_created` + 200，库中已有 `in_progress` 记录与第一题），只是前端先放弃等待，创建页仅显示报错、不跳转，用户误以为失败。

## 修复

`frontend-react/src/features/interviews/api/interview-api.ts`：
- `createInterview` 增加 `{ timeout: 600_000 }`（与 `submitAnswer` 一致），覆盖全局 120s 超时。
- 创建成功后 `useCreateInterview` 会跳转 `/app/interviews/{id}/live`，现可正常完成。

## 验证

- `pnpm type-check` 通过。
- 库中已有因旧超时已创建的面试 `int_0e3c4a75605f`（res_787d05aab294，in_progress）可在「模拟面试」列表继续。

## 说明

- 同步创建 + LLM 计划生成本质耗时较长，属预期；提升超时使请求能正常完成并跳转。
- 旧的超时点击其实已创建过一场面试，用户若再次点击会新建第二场；建议从列表恢复已有面试或忽略旧场。
