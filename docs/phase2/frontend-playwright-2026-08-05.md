# Phase 2: Playwright E2E 测试启用完成

**日期**: 2026-08-05  
**状态**: ✅ 完成  
**任务**: Task #35 — 启用并运行 Playwright E2E 测试

---

## 目标

为前端接入 Playwright E2E 测试，覆盖关键用户流程（认证 → 工作台 → 简历 → 面试 → 报告），并跑通完整套件。此前前端只有 vitest 风格组件测试，缺少真实浏览器端的集成验证。

---

## 实现内容

### 1. 配置 (`frontend-react/playwright.config.ts`)

- **testDir**：`./e2e`
- **baseURL**：`http://localhost:5174`
- **关键修复**：`launchOptions: { args: ['--no-sandbox', '--disable-gpu'] }` —— Windows 上 headless Chromium 默认参数会 crash（"session closed" protocol 错误），显式禁用沙箱与 GPU 后稳定
- **workers**：`process.env.CI ? 1 : 2`（本地 2 worker，CI 串行）
- **reporter**：`html`；trace 仅在 retry 时采集；失败自动截图
- **webServer**：`pnpm dev`（vite），`reuseExistingServer: !CI`，启动超时 120s

### 2. 认证工具 (`e2e/utils/auth.ts`)

应用路由在 `/app/*` 下、由 `ProtectedRoute` 守卫，E2E 需要真实登录态。为避免每次走 UI 登录：

- `registerUser(request)`：通过后端 API `POST /api/v1/auth/register` 注册新用户，返回 token
- `setupAuthenticatedPage(page, request)`：注册用户 → `GET /api/v1/me` 取 profile → `page.addInitScript` 在页面加载前向 `localStorage` 写入 `auth-storage`（Zustand persist 格式 `{state: {token, user}, version: 0}`），使应用启动即为已登录态

### 3. 测试用例（5 个 spec，22 个用例）

| Spec | 覆盖 |
|------|------|
| `auth.spec.ts` | 登录页渲染、API 注册/登录、`/me` 有效 token、无效 token 401 |
| `dashboard.spec.ts` | 工作台加载、导航菜单（简历管理/模拟面试）、跳转简历页、健康检查 |
| `interview.spec.ts` | 面试列表/空态、创建入口、详情跳转、SSE 房间（无面试时条件跳过） |
| `report.spec.ts` | 报告页导航、有报告时展示 section、报告 API 200/404 |
| `resume-upload.spec.ts` | 上传入口、简历列表、详情跳转（文件上传用例保持 `test.skip`） |

> 空数据兼容：`interview.spec.ts` / `report.spec.ts` / `resume-upload.spec.ts` 中依赖「已有数据」的用例，在无数据时 `test.skip()`，避免污染共享开发库。

### 4. npm scripts

```
test:e2e:          "playwright test"
test:e2e:ui:       "playwright test --ui"
test:e2e:debug:    "playwright test --debug"
test:e2e:headed:   "playwright test --headed"
test:e2e:report:   "playwright show-report"
```

---

## 验证

```bash
✅ cd frontend-react && pnpm test:e2e    # 17 passed / 5 skipped / 0 failed (35.8s)
✅ echo $?                              # 退出码 0
✅ pnpm type-check                      # 0 errors
✅ pnpm lint                            # 0 errors
```

> 前置条件：后端运行在 `localhost:8000`（`uvicorn app.main:app --port 8000`）且 PostgreSQL 可达。此前一次 run 退出码为 1，根因是后端未启动 / 偶发 Chromium crash；重启后端后稳定通过。

---

## 手动测试检查清单
- [ ] `pnpm test:e2e` 完整套件退出码 0
- [ ] auth spec 覆盖登录页 + API 认证
- [ ] dashboard 导航、健康检查通过
- [ ] interview / report / resume spec 在空库与有数据两种情况下均不红

---

## 下一步

- 待办任务 #15（并发面试负载测试）仍 pending，非前端。
- 新任务文档：#34 ESLint（见 `frontend-eslint-2026-08-05.md`）。

---

**创建时间**: 2026-08-05  
**实施者**: Claude Code
