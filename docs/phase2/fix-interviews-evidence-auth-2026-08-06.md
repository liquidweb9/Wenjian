# 修复：interviews / evidence 路由缺失鉴权与所有权

**日期**: 2026-08-06
**状态**: ✅ 完成

---

## 背景

第二轮端点安全审计（Codex 未能完成，由本 session 自行完成）发现 `app/api/v1/interviews.py` 与 `app/api/v1/evidence.py` **整条路由均无鉴权、无所有权校验**，任何调用者都可以：

- 读取/提交/结束任意用户的面试（含写操作）
- 订阅任意面试的 SSE 事件流
- 读取任意用户的验证点、证据、转移记录、矛盾记录

这是与 `resumes.py` 同级别的 CRITICAL 水平越权漏洞。

## 修复

### `app/api/v1/interviews.py`（6 个端点）

- 全部端点加入 `user: Annotated[User, Depends(get_current_user)]`。
- `GET ""`（列表）→ 按 `Interview.user_id` 过滤。
- `POST ""`（创建）→ 校验 resume 属于当前用户（否则 404），并把 `user.user_id` 写入 `Interview.user_id`。
- `GET /{id}`、`POST /{id}/answers`、`POST /{id}/finish` → 按 `user_id` 过滤（非本人 404）。
- `GET /{id}/events`（SSE）→ 订阅前先校验所有权（`_interview_owned_by`）。

### `app/api/v1/evidence.py`（4 个端点）

- 全部端点加入 `get_current_user`。
- 新增三个所有权辅助函数：
  - `_vp_owned_by`：验证点 → claim → resume → user
  - `_claim_owned_by`：claim → resume → user
  - `_interview_owned_by`：interview → user
- `GET /verification-points/{claim_id}` → `_claim_owned_by`
- `GET /transitions/{vp_id}` / `GET /evidence/{vp_id}` → `_vp_owned_by`
- `GET /contradictions/{interview_id}` → `_interview_owned_by`
- 非本人资源统一返回 404（不暴露存在性）。

## 关联修改

- `tests/test_evidence_api.py`：重写为注册用户 + 通过 `async_session_factory` 播种所有权数据（resume/claim/verification_point/interview），携带 bearer token 调用；新增 2 个越权（404）测试。播种处显式 `flush()` 父表以符合 PG FK 顺序。

## 验证

- `tests/test_evidence_api.py` → 10 passed（含 2 个新越权测试）。
- 完整后端套件 → **591 passed, 0 failed, 0 errors**。

## 说明

- `answer_diff.py`、`abilities.py`、`job_targets.py`、`claim_gap.py`、`training_plans.py` 经审计均已包含 `get_current_user` + 所有权校验，无需改动。
- 需重启后端进程使安全修复生效（开发服务器仍运行旧代码）。
