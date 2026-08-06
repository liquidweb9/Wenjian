# 修复：结束面试接口 120s 前端超时（finishInterview）

**日期**: 2026-08-07
**状态**: ✅ 完成

---

## 问题报告

面试房间里点击「结束面试」后，控制台报：

```
interview-room-page.tsx:221  Uncaught (in promise) ApiError: timeout of 120000ms exceeded
    at api-client.ts:63:11
    at async Object.finishInterview [as mutationFn] (interview-api.ts:131:20)
```

点击「继续」后仍能继续答题。

## 根因

与 `createInterview`、`submitAnswer` 完全相同的模式：axios 全局超时 120s（`api-client.ts`），而 `finishInterview` 没有像另外两个接口那样覆盖超时。

`POST /interviews/{id}/finish` 会通过 `Command(resume=..., update={next_action: FINISH})` 驱动 LangGraph 跑完 `generate_report_node`（一次大 LLM 调用 + 聚合证据/能力/训练计划的确定性汇总），120s 内正常完成不了。

**为什么点击继续还能答题**：axios 在 120s 中止请求时，uvicorn 会取消正在处理的 handler → 图的 ainvoke 被中断 → 面试没有被标记为 finished → 用户继续答题。并非后端逻辑错误，而是请求被客户端提前掐断。

## 修复

`frontend-react/src/features/interviews/api/interview-api.ts` 的 `finishInterview` 加入 `timeout: 600_000`（与 `createInterview`、`submitAnswer` 一致）：

```ts
export async function finishInterview(interviewId: string) {
  const { data } = await api.post(
    `/interviews/${interviewId}/finish`,
    undefined,
    {
      // generate_report aggregates evidence, ability observations, and training
      // plan — LLM-heavy, routinely exceeds the global 120s timeout even when
      // the server completes normally.
      timeout: 600_000,
    },
  )
  return data
}
```

## 验证

- `pnpm type-check` 通过（0 error）。
- 房间页已有 finished 态渲染：收到 `interview.finished` / `report.ready` SSE 后，`isFinished=true`，结束按钮隐藏，主区出现「查看报告」按钮（`interview-room-page.tsx:536-563`）→ 无需额外跳转逻辑。
- 后端 `generate_report_node` 为单次 LLM 调用 + 确定性汇总，无死循环（`app/interview/nodes/generate_report.py:40-46`）。

## 备注

- `finish_interview` 后端当前**没有**调用 `_ensure_graph_checkpoint`（与 `submit_answer` 不同）。若进行中面试的内存图状态丢失/损坏，`interview_graph.ainvoke` 失败会走 try/except，仍会标记 finished 但 `final_report=None`（无报告、报告页显示「报告正在整理中」）。若用户复测时遇到「结束成功但无报告」，需要给 finish 路径补上同样的 checkpoint 重建逻辑。
