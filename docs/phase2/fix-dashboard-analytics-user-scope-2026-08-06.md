# 修复：dashboard / analytics 聚合统计未按用户隔离

**日期**: 2026-08-06
**状态**: ✅ 完成

---

## 问题报告

用户在测试中发现：简历管理页面为空、模拟面试列表为空，但 dashboard 却显示「已上传简历 70」「累计面试 16」，数字对不上。

## 根因

`/api/v1/dashboard/summary`（`app/api/v1/dashboard.py`）与 `/api/v1/analytics/summary`、`/analytics/trends`（`app/api/v1/analytics.py`）在 M2.6 安全加固中被遗漏：

- **无 `get_current_user` 鉴权**：未登录也可访问。
- **所有查询未按 `user_id` 过滤**：计数的是**全库**简历/面试（70 份简历、16 场面试——其中大部分是历史测试用户的数据，还有 9 份简历、4 场面试的 `user_id` 为 NULL 的孤儿数据）。

而简历列表页（`resumes.py`）与面试列表页（`interviews.py`）已按当前用户过滤。于是同一个账号：列表页显示 0，dashboard 却显示全局 70/16。

这不仅是数字不一致，还构成**越权数据泄露**：dashboard 的「最近使用的简历」「进行中的模拟面试」区块会把其他用户的简历与面试展示给当前用户。

## 修复

### `app/api/v1/dashboard.py`
- 加入 `get_current_user`，`/summary` 需登录。
- 全部查询追加 `user_id == user.user_id` 过滤：简历总数、待确认简历数（需 join `ResumeSource`）、面试总数/已完成/进行中、最近简历、进行中面试列表。
- 平均分查询 join `Interview` 并按用户过滤（原来 `select(InterviewReport.data).limit(100)` 是全库取前 100 份报告）。

### `app/api/v1/analytics.py`
- `/summary` 与 `/trends` 均加入 `get_current_user`。
- 面试计数与报告读取全部 join `Interview` 并按用户过滤。

## 测试

新增 `tests/test_dashboard_analytics.py`（6 个用例）：
- 无 token 访问 dashboard / analytics → 401。
- 用户 A（2 简历 + 2 面试）只见自己的数据；用户 B（1 简历）只见自己的数据。
- `recent_resumes` / `in_progress_interviews` / `interviews_over_time` / `score_trend` 均按用户隔离。

## 验证

- `tests/test_dashboard_analytics.py` → 6 passed。
- 完整后端套件 → 597 passed, 0 failed, 0 errors（原 591 + 新增 6）。
- 重启后端后实测：无 token 访问 `/dashboard/summary`、`/analytics/summary` → **401**；`test@wenjian.ai` 登录后 dashboard 显示 0/0，与空列表一致。

## 说明

- 数据库中的 70 份简历 / 16 场面试是**全库历史测试数据**（多个测试用户 + 9 份无主孤儿简历），不是当前登录账号的数据。修复后每个账号只看到自己的数据，dashboard 与列表页数字一致。
- 孤儿数据（`user_id IS NULL`）不归属任何用户，无法在任意账号下显示；如需清理可单独处理。
