# 修复：提交回答 500（EvidenceSpanExtractor id_generator）+ 后端 DB 凭据失效

**日期**: 2026-08-07
**状态**: ✅ 完成

---

## 问题一：提交回答返回 500

### 现象
`POST /api/v1/interviews/{id}/answers` 返回 500，后端日志：
`EvidenceSpanExtractor.__init__() got an unexpected keyword argument 'id_generator'`，错误点在 `app/interview/nodes/update_evidence.py:82`。

### 根因
`update_evidence.py` 同时构造两个组件时都传了 `id_generator`：
- `EvidenceSpanExtractor(llm=llm, id_generator=...)` —— **该类构造函数不接受 `id_generator`**（证据 ID 由调用方自行 `new_id("ev")` 生成，提取器不负责）。
- `ContradictionDetector(llm=llm, id_generator=...)` —— 该类接受（用于生成 contradiction_id）。

构造发生在 `async with` 的 try 块**之前**，所以异常直接冒泡到图执行层，整个回答处理失败（没有被节点的 Phase 1 fallback 兜住）。

### 修复
`app/interview/nodes/update_evidence.py:82`：
```python
span_extractor = EvidenceSpanExtractor(llm=llm)   # 移除 id_generator
contradiction_detector = ContradictionDetector(llm=llm, id_generator=lambda: new_id("ct"))
```

## 问题二：重启后端后数据库连接全部失败

### 现象
重启后端后，登录/所有 DB 操作失败；postgres 日志显示 `password authentication failed for user "postgres"`；asyncpg 侧表现为 `connection was closed in the middle of operation`。

### 根因（操作问题，非代码）
前一步 `cd frontend-react` 后 Bash 工作目录停留在 `frontend-react`。重启 uvicorn 时进程从该目录启动，pydantic-settings 按 CWD 找 `config.env` 找不到，回落到默认 `postgres:postgres` —— **密码不对**，被 postgres 拒绝。（此前后端从项目根启动能找到真实 `config.env`。）

期间为排查误重启了 postgresql-x64-18 服务（无副作用，数据持久化）。

### 修复
后端改为**从项目根目录**启动：`cd /d/work/project/deep_interview_agent && python -m uvicorn app.main:app --port 8000`。连接恢复。

## 验证

- 重启后登录 200、`GET /me` 200、`GET /interviews` 200。
- 实测在真实面试上提交回答 → **200**，turn_count=1，正常生成下一题。
- 说明：项目使用 **内存检查点**（LangGraph InMemorySaver），后端重启会丢失进行中面试的图状态；`_ensure_graph_checkpoint` 会从数据库（问题/回答/画像）重建，实测可用。生产部署应考虑持久化检查点。
