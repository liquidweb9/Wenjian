# 前端：页面导航与页头样式统一（BackButton / PageHeader）

**日期**: 2026-08-07
**状态**: ✅ 完成

---

## 背景

各页面返回导航与页头样式不一致：有的页面有面包屑、有的没有；返回按钮散布在表单底部、右上角等多个位置；创建按钮样式互不相同（蓝/深色/主色）；简历管理页带 Logo 而其他管理页没有；设置页没有返回入口。本次统一了全部页面的页头与返回导航，并修复两个小问题。

## 修改内容

### 1. 统一返回导航组件

新建 `frontend-react/src/components/common/back-button.tsx`：

- 组件 `BackButton`：ArrowLeft 图标 + 文字，`to` 指定目标路由，`label` 默认「返回」。
- 基础样式含 `alignSelf: "flex-start"`，避免在 `PageHeader` 的 flex 列容器中拉伸占满整列（修复「返回键拉得很长」）。

扩展 `frontend-react/src/components/common/page-header.tsx`：

- 新增 `back?: { to: string; label?: string }` prop，渲染在标题上方。
- 页头规则统一为：
  - **管理/列表页**（工作台、简历管理、模拟面试、目标岗位、能力分析、设置）：`PageHeader` + 描述 + `btn-primary` 创建按钮，**无 Logo**、**无返回**。
  - **创建/详情页**（上传简历、创建面试、创建岗位、简历画像/审阅/主张、能力档案、训练计划、能力缺口、目标岗位详情）：`PageHeader` + `brand` Logo + 左上角返回按钮。

### 2. 各页面统一改动

| 页面 | 改动 |
| --- | --- |
| `resume-upload-page` | 自定义 h2/返回 → `PageHeader`（brand + back） |
| `resume-list-page` | 移除 `brand` Logo，与其他管理页一致 |
| `resume-review-page` | 标题行 → `PageHeader`，状态徽标放入 `action` 槽 |
| `resume-claims-page` | 标题行 → `PageHeader`，「能力档案/训练计划」改 `btn-secondary`、「分析能力缺口」改 `btn-primary`，数量移入描述 |
| `resume-profile-page` | 已在上一轮统一，保持不变 |
| `interview-list-page` | 自定义 h2 + 深色按钮 → `PageHeader` + `btn-primary`「新建面试」 |
| `job-target-list-page` | **整体重写**：移除自定义 `padding:32px` 容器与蓝色按钮；改用 `PageHeader` + `btn-primary`「创建新岗位」；卡片改用 `app-surface`/CSS 变量；加载/错误/空态改用 `LoadingState`/`ErrorState`/`EmptyState` |
| `job-target-create-page` | 移除 `padding:32px` 容器；`BackButton + h1` → `PageHeader`（brand + back） |
| `job-target-detail-page` | 移除面包屑与自定义头部；`PageHeader`（back + title + 操作按钮）；操作按钮改 `btn-primary`/`btn-secondary`/`btn-danger`；加载/错误改用 `LoadingState`/`ErrorState`；移除 `padding:32px` 容器 |
| `claim-gap-page` | 移除面包屑与自定义卡片；`PageHeader`（back + action「重新分析」）；加载/错误/空态改用 `LoadingState`/`ErrorState`/`EmptyState`；移除 `padding:24px` 容器 |
| `ability-profile-page` | hero 卡片头 → `PageHeader`（back），移除 `title`/`subtitle` 样式 |
| `training-plan-page` | hero 卡片头 → `PageHeader`（back + action「生成训练计划」），统计卡移入独立 `app-surface` 区块 |
| `interview-room-page` / `interview-report-page` | 已在上一轮统一，保持不变 |

### 3. 顶栏与文档标题修复

- `frontend-react/src/lib/brand.ts`：`PAGE_TITLES` 补充 `/app/job-targets`（目标岗位）、`/app/job-targets/create`（创建目标岗位），修复顶栏标题错误显示「工作台」。
- `job-target-detail-page.tsx` / `claim-gap-page.tsx`：补充 `usePageTitle` 调用，设置正确文档标题。

### 4. 模板岗位名称只读

`job-target-detail-page.tsx`：

- 编辑表单中，当 `jobTarget.source === "template"`（预设模板创建）时，岗位名称输入框 `disabled`、置灰（新增 `inputDisabled` 样式）、悬停提示「预设模板的岗位名称不可修改」。其余字段仍可编辑。

## 验证

- `pnpm type-check` 通过（tsc 0 error）。
- `eslint src` 0 error（24 条既有 warning，无新增）。
- `vite build` 成功。
- Playwright 实测：
  - 目标岗位列表/详情/创建、简历列表/上传、面试记录、能力分析、设置页头与返回导航渲染正确。
  - 返回按钮宽 130px，不再拉伸占满父容器（父容器 187px）。
  - 模板岗位编辑时名称输入框 `disabled: true`。

## 说明

- 面试房间（`interview-room-page`）与面试报告页为全屏特殊页，保留其独有头部布局。
- 页面级样式仍以 `React.CSSProperties` 内联为主，`PageHeader`/`BackButton`/`LoadingState`/`ErrorState`/`EmptyState` 为共享组件。
