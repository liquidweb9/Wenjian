# 前端：SSE 连接状态异常（一直显示「连接中」）修复记录

**日期**: 2026-08-07
**状态**: ✅ 完成

---

## 问题现象

进入模拟面试房间后，页面顶部连接状态一直显示「连接中」，但题目内容、历史记录等 REST 数据均正常展示。即使 SSE 建立失败也会不断重连，永不进入「已连接」。

## 根因分析

页面有两条独立的数据通道，基地址不一致：

1. **REST 请求**（axios）：`src/lib/api-client.ts` 使用 `env.VITE_API_BASE_URL`（本项目 `.env` 中为 `http://localhost:8010`）拼出 `/api/v1`，正常连通。
2. **SSE 实时通道**（`fetch`）：`src/features/interviews/api/interview-sse.ts` 原本使用**相对路径** `/api/v1/interviews/{id}/events`。该请求被 Vite dev server 代理转发到 `vite.config.ts` 写死的 `target: 'http://localhost:8000'`，而后端实际运行在 **8010** 端口。

于是 SSE fetch 始终连不上 8000，`interview-sse.ts` 中 `onConnectionChange("connected")` 永远不触发，客户端进入无限重连（`connecting` → `disconnected` → `reconnecting`），表现为一直「连接中」。

REST 与 SSE 基地址不一致，是状态显示「连接中」但题目能展示的直接原因。

## 修复内容

### 1. 实际使用的 SSE 连接（`interview-sse.ts`）

- 新增 `SSE_BASE_URL`，从 `env.VITE_API_BASE_URL` 拼出 `/api/v1`。
- fetch URL 由相对路径 `/api/v1/interviews/${interviewId}/events` 改为 `${SSE_BASE_URL}/interviews/${interviewId}/events`，与 axios 同源。

### 2. 疑似死代码（`interview-api.ts` 的 `getInterviewEvents`）

- 该函数当前无任何调用方，但同样存在相对路径硬编码问题，为防后续误用一并修正为 `env.VITE_API_BASE_URL`。

### 3. 全量检查运行时硬编码

- `grep` 全前端确认：运行时代码已无写死的后端地址。
- 剩余 `localhost:8000` 仅存在于 `vite.config.ts`（dev 代理）、`package.json`（api:generate）、`e2e/*`、`playwright.config.ts`（测试约定）、`env.ts`（默认值兜底，被 `.env` 覆盖），均为非运行时代码，保留不动。

## 验证

- `pnpm type-check` 通过。
- 重启 dev server（Vite 需重新读取 env）后，SSE 连接应进入「已连接」，不再停留在「连接中」。

## 关联改动

- `interview-room-page.tsx`：主区域「正在恢复面试现场」（`isTransitioning`）与题目/等待问题/分析进度三个渲染块已加互斥条件，避免连接恢复期间题目与恢复提示同屏展示。
