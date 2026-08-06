# 修复：登录 / 注册 401 报错（token 未先持久化）

**日期**: 2026-08-06
**状态**: ✅ 完成
**任务**: Task #50 — 登录点击报错

---

## 问题

用户在浏览器点击「登录」报错。后端日志显示：

```
POST /api/v1/login  → 200 OK      （登录成功，token 已签发）
GET  /api/v1/me     → 401         （获取用户资料失败）
```

**根因**：`login-form.tsx` 中 `getMe()` 在 `setAuth()` 之前调用。axios 请求拦截器从
`localStorage["auth-storage"]` 读取 token 注入 `Authorization` 头；而此时 token 尚未写入
store（因此未持久化到 localStorage），`GET /me` 不带 bearer 头 → 401 → 整个登录流程抛错。

`register-form.tsx` 存在完全相同的 bug。

## 修改

### `frontend-react/src/stores/auth-store.ts`
- 新增 action `setToken(token)`：仅持久化 token 并置 `isAuthenticated = true`（不要求 user）。

### `frontend-react/src/features/auth/components/login-form.tsx`
- `handleSubmit` 顺序调整：`login()` → `setToken(token)` → `getMe()` → `setAuth(token, user)`。
- 新增 `setToken` 订阅。

### `frontend-react/src/features/auth/components/register-form.tsx`
- 相同顺序调整。

## 验证

- `pnpm type-check` — 0 errors
- `pnpm lint` — 0 errors（23 个既有 warning，非本次改动引入）
- Playwright 实机验证：
  - `POST /api/v1/login` → 200
  - `GET /api/v1/me` → 200（此前 401）
  - 登录后跳转 `/app/dashboard`，顶部栏展示 `test@wenjian.ai`，认证态正常渲染

## 关键点

Zustand `persist` 对 localStorage 采用同步写，`setToken()` 返回后拦截器即可读到 token，
因此 `getMe()` 能正确携带 bearer 头。
