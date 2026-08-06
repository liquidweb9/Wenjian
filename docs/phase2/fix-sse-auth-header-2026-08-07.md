# 修复：面试房间 SSE 连接 401（缺 Authorization 头）

**日期**: 2026-08-07
**状态**: ✅ 完成

---

## 问题报告

进入面试房间后 SSE 事件流报 `GET /api/v1/interviews/{id}/events 401 (Unauthorized)`，页面提示「连接已断开」，无法继续面试。

## 根因

M2.6 给 `GET /interviews/{id}/events`（SSE）加了 `get_current_user` + 所有权校验，但前端 SSE 用的是**原生 `fetch`**（`interview-sse.ts:19`），不走 axios 拦截器，因此**没有携带 Authorization 头** → 后端 401。

axios 客户端（`api-client.ts`）通过拦截器从 `localStorage["auth-storage"]` 注入 token，而 `fetch` 路径缺失这层。

## 修复

- `api-client.ts`：新增并导出 `getAuthToken()`（从 localStorage 读取 token），axios 请求拦截器改用该助手。
- `interview-sse.ts`：`createSSEConnection` 的 fetch 请求头加入 `Authorization: Bearer <token>`。
- `interview-api.ts`：同步修复同模式的 `getInterviewEvents`（未使用但同隐患）。

## 验证

- `pnpm type-check` 通过，lint 0 error。
- 实测：`GET /interviews/int_0e3c4a75605f/events` 无 token → **401**；带 token → **200**（流式正常建立）。
- 用户刷新房间页后 SSE 即重新连上。
