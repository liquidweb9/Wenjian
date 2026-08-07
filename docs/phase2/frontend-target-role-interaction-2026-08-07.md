# 前端：目标岗位交互细化（保存/修改文案、按钮禁用、模板名称锁定）

**日期**: 2026-08-07
**状态**: ✅ 完成

---

## 背景

简历详情页与目标岗位新建页的目标岗位交互在验收中发现问题：文案未区分「保存/修改」、无改动时按钮仍可点击、从预设模板创建时岗位名称可被随意修改。

## 修改内容

### 1. 简历详情页 — 保存/修改目标岗位文案区分

`frontend-react/src/features/resumes/pages/resume-review-page.tsx`：

- **按钮文案**：无目标岗位 → 「保存目标岗位」；已有目标岗位 → 「修改目标岗位」。
- **说明文案**：未绑定时「保存目标岗位后，主张将按新岗位重新排序（保留手动禁用的主张）。」；已绑定时「修改目标岗位会按新岗位重新排序已有主张（保留手动禁用的主张）。」
- **成功提示**：分别显示「目标岗位已保存…」/「目标岗位已修改…」，均注明主张已按新岗位重新排序。

### 2. 简历详情页 — 无变化时禁用按钮

同文件：

- 新增 `hasTargetRoleChange` 判断：`job_target_id` 与 `target_role` 任一项与当前已存值不同即为有改动。
- 按钮 `disabled={targetRoleMutation.isPending || !hasTargetRoleChange}`，禁用态背景置灰（`#cbd5e1`）。

### 3. 目标岗位新建页 — 模板岗位名称锁定

`frontend-react/src/features/job-target/pages/job-target-create-page.tsx`：

- 从预设模板创建（`mode === "template"`）时，岗位名称输入框 `disabled`，置灰（新增 `inputDisabled` 样式），悬停提示「预设模板的岗位名称不可修改」。
- 「从空白创建」与「粘贴 JD」模式仍可自由编辑岗位名称。

## 验证

- `pnpm type-check` 通过。
- 涉及路由：`/app/resumes/:resumeId`（简历解析确认页）、`/app/job-targets/create`（创建目标岗位）。

## 说明

- 保存与修改目标岗位走同一个 `PATCH /resumes/{id}/target-role` 端点，仅前端文案与禁用态区分，后端无改动。
