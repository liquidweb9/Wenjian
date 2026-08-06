# 修复：E2E 异步基础设施 + 简历所有权安全漏洞

**日期**: 2026-08-06
**状态**: ✅ 完成

---

## 背景

完整后端测试套件存在一批既有失败（非本 session 引入的回归）：

- `test_auth.py` / `test_e2e_flows*.py` — `asyncpg.InterfaceError: Event loop is closed` / `another operation is in progress`
- `test_data_deletion.py` — sqlite `NOT NULL constraint failed: interviews.thread_id` / `resume_revisions.resume_id`
- 各 e2e 测试与当前 API 契约不一致（分页、路由、schema）
- `test_auth.py::test_cannot_access_other_user_resume_via_api` — 暴露 **`resumes.py` 路由完全没有鉴权/所有权校验**

## 修复清单

### 1. 异步连接池跨事件循环（根因修复）

**问题**：应用全局 async engine 的 asyncpg 连接池会在创建它们的那个事件循环关闭后，被新的请求复用（sync `TestClient` portal loop 与 pytest-asyncio loop 混用）→ `Event loop is closed` / `another operation is in progress`。

**修复**：
- `app/persistence/database.py`：当环境变量 `WJ_TEST_NULL_POOL=1` 时，engine 使用 `poolclass=NullPool`（每次操作新建/关闭连接，不跨循环复用）。生产环境保持默认连接池。
- `tests/conftest.py`：在导入 app 模块**之前**设置 `os.environ.setdefault("WJ_TEST_NULL_POOL", "1")`。

### 2. 测试数据与 ORM 级联（`tests/test_data_deletion.py`）

- `Interview` 构造补上必填 `thread_id`（与 interview_id 一致）、`target_role`。
- `ResumeRevision.status` 从非法值 `"COMPLETE"` 改为合法枚举 `"CONFIRMED"`（`ResumeStatus` 无 COMPLETE）。
- `app/persistence/models.py`：为 `Interview.questions` / `Interview.answers` / `ResumeSource.revisions` 增加 `cascade="all, delete-orphan"`，使 ORM `session.delete()` 删除子记录而非把 NOT NULL FK 置空。

### 3. GDPR 删除的 PostgreSQL 外键级联（`app/core/data_deletion.py`）

**问题**：`DataDeletionService` 直接删除父表（`ResumeSource`/`Interview`），PG 启用 FK 约束时报 `ForeignKeyViolationError`（sqlite 默认关闭 FK 掩盖了此问题）。上传补上 `user_id` 后立刻暴露。

**修复**：重写三个删除方法，**先删子表再删父表**：
- `delete_user_data`：TrainingTask/AbilityProfile/AbilityObservation → LLMCall(审计，删面试前先置空 `interview_id`) → EvidenceTransition/Evidence/Contradiction/InterviewReport/InterviewAnswer/InterviewQuestion → Interview → Claim 映射/VerificationPoint → ResumeClaim/ResumeProfile/ResumeBlock/ResumeRevision → ResumeSource → JobTarget → User。
- `delete_resume` / `delete_interview`：同样改为显式 Core `delete()`，按 FK 顺序删除子记录。

### 4. 简历路由所有权漏洞（`app/api/v1/resumes.py`）

**问题（CRITICAL）**：整个 `resumes` 路由无鉴权、无所有权过滤：
- `GET /resumes/{id}` 可读任意用户简历（测试证实 user2 可读 user1 简历 → 200）
- `GET /resumes` 列出所有用户简历
- 上传不写 `user_id`（所有简历 user_id 为空）
- 所有 PATCH/DELETE 无所有权校验

**修复**：
- 所有端点加入 `user: Annotated[User, Depends(get_current_user)]`。
- 新增 `_resume_owned_by()` 辅助函数；读/写端点对非本人简历统一返回 **404**（不暴露存在性）。
- 上传端点把 `user.user_id` 写入 `ResumeSource.user_id`（`_save_resume_to_db` 新增 `user_id` 参数）。
- 列表端点按 `user_id` 过滤。

### 5. E2E 测试与 API 契约对齐（`tests/test_e2e_flows.py`、`tests/test_auth.py`）

- 所有固定邮箱改为 `f"{prefix}_{pytest.timestamp}@example.com"`（避免持久化 PG 中“已注册”400）。
- `POST /resumes/upload` → `POST /resumes`（上传状态码 200 而非 201）。
- 列表端点断言改为分页结构 `data["items"]`。
- job-target 创建补 `requirements`（`JobTargetCreate` 必填）；`/from-jd` → 创建 `source="pasted_jd"`。
- 上传状态断言更新为 `ResumeStatus` 当前枚举（`PARSED_UNCONFIRMED`）。

## 验证

- `tests/test_auth.py` + `tests/test_data_deletion.py` + `tests/test_e2e_flows.py` + `tests/test_e2e_flows_async.py` → **45 passed**。
- 探针脚本验证：上传 → `DELETE /me`（200）→ 同邮箱重新注册（201）成功。
- 前端：`pnpm type-check` 0 errors、`pnpm lint` 0 errors（23 个既有 warning）。
- 完整后端套件运行中（见 `pytest tests/ -q`）。

## 关键设计点

NullPool 仅在 pytest 下启用（`WJ_TEST_NULL_POOL`），生产仍用连接池；测试隔离优先于池化性能，同时从根源消除跨事件循环的 asyncpg 连接复用。
