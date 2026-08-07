# 修复：确认简历并发写入撞 `resume_profiles_pkey`（merge → 幂等 upsert）

**日期**: 2026-08-07
**状态**: ✅ 完成

---

## 问题报告

用户重试「确认并提取主张」时报错：

```
sqlalchemy.exc.IntegrityError: (asyncpg.exceptions.UniqueViolationError)
重复键违反唯一约束"resume_profiles_pkey"
键值"(profile_id)=(res_136e91a744a2_profile)" 已经存在
```

栈顶位置：`app/api/v1/resumes.py:611` → `await session.execute(sa_delete(DBClaim)...)` 触发 autoflush 时 INSERT 撞主键。

## 根因

`confirm_revision` 里保存画像用的是：

```python
db_profile = DBProfile(profile_id=resume_id + "_profile", ...)
await session.merge(db_profile)
```

profile 主键是**确定性**的 `{resume_id}_profile`。`session.merge` 内部先 SELECT，查不到才走 INSERT；但从 SELECT 到真正 flush 之间隔着 ~24s 的 LLM 主张提取调用。同一简历出现并发/重试确认时，两条事务的 SELECT 都发生在对方 INSERT 之前 → 都判定为 INSERT → 后提交者撞唯一约束。

佐证：日志 06:13:18 有一次 `claims_count=0` 的确认成功（profile 已落库，revision `rev_105cebb1e484`），06:13:24 又一次 `claims_extracted count=9`，两条事务交错在 ~24s LLM 窗口内。

## 修复

`app/api/v1/resumes.py`：`session.merge` 换成 PostgreSQL 幂等 upsert：

```python
from sqlalchemy.dialects.postgresql import insert as pg_insert

profile_upsert = pg_insert(DBProfile).values(...)
profile_upsert = profile_upsert.on_conflict_do_update(
    index_elements=[DBProfile.profile_id],
    set_={..., "revision_id": profile_upsert.excluded.revision_id, "data": profile_upsert.excluded.data, ...},
)
await session.execute(profile_upsert)
```

并发插入同一主键不再报错；重确认走 `DO UPDATE`（保留原 `created_at`）。

## 验证

- 并发复现脚本：两条事务同时 upsert 同一 `profile_id` 全部成功，无 UniqueViolation，最终行最后写入者生效。
- `ruff check app/api/v1/resumes.py` 通过。
- `pytest tests/ -q` → 599 passed。

## 附：本次会话同链修复（LLM 接入）

本轮排查过程中一并修复的 LLM 相关配置问题（详情见各自根因）：

1. **LLM 切换 DeepSeek**：`config.env` → `https://api.deepseek.com/v1`、key `sk-8104f6757f9e4e849898d397f473e858`、三 tier 模型 `deepseek-v4-flash`（弃用 sui-xiang，其网关有 ~60s 上游超时，非流式长任务必断）。
2. **推理模型烧 token**：`deepseek-v4-flash` 是推理模型，不加 `reasoning_effort="none"` 会把 max_tokens 全烧在 `reasoning_content`、`content` 为空 → JSONDecodeError。`app/llm/agnes_api.py` 的 `generate_structured`/`generate_text` 增加 `reasoning_effort="none"` 默认参数（profile 构建 60s+ → ~17s）。
3. **max_tokens 截断**：`LLM_MAX_TOKENS` 4096→8192（config.env + config.py 默认）。主张提取实际需 ~4550 tokens，4096 截断导致 `claim_extraction_failed` → `claims_count=0`。
4. **SSL 重试**：`app/llm/retry.py` 增加 `except (httpx.TransportError, ssl.SSLError)` 指数退避重试（1s/2s），覆盖 sui-xiang `_ssl.c:2580` record layer failure。
5. **流式支持（未启用）**：`agnes_api.py` 重构出 `_chat_completion()`，`generate_structured`/`generate_text` 加 `stream: bool = False` 参数，SSE 聚合 + 兼容 DeepSeek chunk usage。流式可绕开 ~60s 网关超时，为将来换回长延迟提供方预留。
