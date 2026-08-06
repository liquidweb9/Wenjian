# Phase 2: 前端 ESLint 启用完成

**日期**: 2026-08-05  
**状态**: ✅ 完成  
**任务**: Task #34 — 启用 ESLint（frontend-react）

---

## 目标

为 `frontend-react` 接入 ESLint，统一前端代码质量检查，与后端 `ruff check` 对齐，让 CI / 本地都能跑静态检查。此前前端没有 lint 工具，只能依赖 `tsc`。

---

## 实现内容

### 1. 依赖安装

新增 devDependencies：
```
@eslint/js
eslint                      # ESLint 10（flat config）
typescript-eslint           # TS 语言支持
eslint-plugin-react-hooks   # hooks 规则
eslint-plugin-react-refresh # 组件快速刷新规则
globals                     # browser / node 全局变量声明
```

### 2. 配置 (`frontend-react/eslint.config.js`)

采用 **ESLint 10 flat config**（不使用已废弃的 `.eslintrc`）：

- **ignore 列表**：`dist`、`node_modules`、`playwright-report`、`test-results`、`coverage`、`src/generated`（openapi 生成的类型）
- **基础规则**：`js.configs.recommended` + `tseslint.configs.recommended`
- **globals**：合并 `globals.browser` + `globals.node`（e2e 文件用到 node API）
- **plugins**：`react-hooks`（新规则集）+ `react-refresh`
- **关键决策**：`react-hooks/set-state-in-effect: 'off'` —— 本项目有意使用「effect 内 setState 同步派生状态」模式，与官方推荐冲突，显式关闭以免误报
- **no-unused-vars**：启用 `^_` 前缀变量豁免（如 `_event` 等占位参数）
- **react-refresh/only-export-components**：降为 `warn`（页面组件文件同时导出 hook / 配置对象是既有模式）

### 3. 修复的 15 个 lint error

- 移除未使用的 import / props（`EvidenceSpanViewer.tsx`、`JDCoverageSection.tsx`、`UnresolvedIssuesSection.tsx`、`resume-list-page.tsx` 的 `ArrowRight`/`FileText`）
- 移除冗余 state（`requirement-editor.tsx` 的 `showAddForm`、`job-target-create-page.tsx` 的 `selectedTemplate`）
- `interview-create-page.tsx` 的 `confirmedResumes` 提取为 `useMemo`
- `training-plan-page.tsx`：`statusBadge` 提取为独立函数、`styles` 加 `Record<string, React.CSSProperties>` 类型，消除 `no-explicit-any`

### 4. npm scripts

```
lint: "eslint ."
```

---

## 验证

```bash
✅ cd frontend-react && pnpm lint          # 0 errors, 23 warnings（仅 react-refresh 提示，非阻塞）
✅ cd frontend-react && pnpm type-check    # 0 errors
```

> 剩余 warnings 全部为 `react-refresh/only-export-components`（页面文件同时导出组件与非组件），属既有代码模式，保持 warn 级别不阻塞。

---

## 下一步

- 后续 PR 可把 lint 加入 CI，配合后端 `ruff check`。
- 新任务文档：#35 Playwright E2E（见 `frontend-playwright-2026-08-05.md`）。

---

**创建时间**: 2026-08-05  
**实施者**: Claude Code
