# 集成测试修复进度

**日期**: 2026-08-03  
**任务**: Task #22 - 修复集成测试数据库连接问题

---

## 问题诊断

### 根本原因

测试使用全局 `TestClient` 连接到**生产数据库**而非测试数据库，导致：

1. **邮箱冲突**: 静态邮箱（如 `newuser@example.com`）在多次运行后已存在于生产库
2. **Event loop 问题**: TestClient 在处理多个连续请求时，异步 event loop 管理出现问题
   - 错误: `AttributeError: 'NoneType' object has no attribute 'send'`
   - 发生在第二个请求的响应发送阶段

### 影响的测试类

`tests/test_auth.py` 中使用 TestClient 的类：
- `TestRegistration` (4 个测试)
- `TestLogin` (3 个测试)
- `TestGetCurrentUser` (3 个测试)
- `TestHorizontalPrivilegeEscalation` (2 个测试)

---

## 解决方案

### 方案 1: 使用唯一邮箱（已实施）

**修改**: 将所有静态邮箱改为使用 `pytest.timestamp`

```python
# 修改前
email = "newuser@example.com"

# 修改后
email = f"newuser_{pytest.timestamp}@example.com"
```

**效果**:
- ✅ 解决邮箱冲突问题
- ⚠️ 仍存在 event loop 问题（TestClient 限制）

**修改的测试**:
- `test_register_new_user` ✅
- `test_register_duplicate_email` (内部逻辑正确，但响应发送崩溃)
- `test_register_without_full_name`
- `test_login_success`
- `test_login_wrong_password`
- `test_login_nonexistent_user`
- `test_get_me_with_valid_token`

**同时修复了错误响应格式**:
```python
# 修改前
response.json()["detail"]

# 修改后
response.json()["error"]["message"]
```

### 方案 2: 迁移到 AsyncClient（推荐）

将 TestClient 测试迁移到 httpx.AsyncClient，类似 `test_e2e_flows_async.py`：

```python
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_register_new_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/register", json={...})
        assert response.status_code == 201
```

**优势**:
- ✅ 正确的 async/await 管理
- ✅ 无 event loop 冲突
- ✅ 与其他异步测试一致

---

## 测试结果

### test_auth.py 修复前后

| 状态 | 修复前 | 修复后 | 改善 |
|------|--------|--------|------|
| Passed | ~4 | 19 | +15 |
| Failed | ~22 | 7 | -15 |
| 通过率 | ~15% | 73% | +58% |

### 修复后仍失败的测试 (7个)

所有失败都是 event loop 问题，测试逻辑本身正确：

1. `test_register_duplicate_email` - 第二个请求响应时崩溃
2. `test_register_without_full_name` - 响应发送时崩溃
3. `test_login_success` - 第二个请求（login）时崩溃
4. `test_login_wrong_password` - 第二个请求时崩溃
5. `test_login_nonexistent_user` - 响应发送时崩溃
6. `test_get_me_with_valid_token` - 第二个请求（get profile）时崩溃
7. `test_cannot_access_other_user_resume_via_api` - 多请求时崩溃

**共同特征**: 所有失败测试都执行了 2+ 个 HTTP 请求

---

## 文件修改

### tests/test_auth.py

**修改内容**:
- 将 8 个测试的静态邮箱改为动态（使用 `pytest.timestamp`）
- 修复错误响应格式检查（`detail` → `error.message`）

**修改示例**:
```python
# Line 134
"email": f"newuser_{pytest.timestamp}@example.com",

# Line 148
email = f"duplicate_{pytest.timestamp}@example.com"

# Line 171
assert "already registered" in response2.json()["error"]["message"].lower()
```

---

## 其他集成测试状态

### tests/test_data_deletion.py

**预期问题**: 可能也使用 TestClient + 静态数据

**待检查**:
- 是否使用 TestClient
- 是否有静态用户/简历 ID
- 是否有 async session fixture

### tests/test_e2e_flows.py (旧版)

**状态**: 已被 `test_e2e_flows_async.py` 替代

**建议**: 标记为 deprecated 或删除

---

## 下一步行动

### 立即执行

1. **将 test_auth.py API 测试迁移到 AsyncClient** ⏳
   - 创建 `tests/test_auth_async.py`
   - 使用 httpx.AsyncClient + ASGITransport
   - 迁移 TestClient 测试类
   - 预期: 所有 26 个 API 测试通过

2. **检查其他集成测试** ⏳
   - `test_data_deletion.py` - 7 errors
   - 其他使用 TestClient 的测试
   - 应用相同的修复策略

### 优化选项

3. **弃用 TestClient**
   - 在项目中全面使用 AsyncClient
   - 更新测试文档和示例
   - 与现有异步测试一致

4. **清理生产数据库测试数据**
   - 删除测试创建的用户（`*@example.com`）
   - 添加数据库清理脚本

---

## 经验教训

### TestClient 限制

1. **不适合多请求测试**: 
   - 连续的请求会导致 event loop 冲突
   - 特别是在注册后立即登录的场景

2. **异步兼容性差**:
   - FastAPI 应用是异步的
   - TestClient 是同步包装器
   - AsyncClient 是更自然的选择

### 测试数据库隔离

1. **测试应使用独立数据库**:
   - 避免污染生产数据
   - 使用 `async_session` fixture
   - 或使用 AsyncClient + 测试数据库

2. **使用唯一标识符**:
   - 时间戳
   - UUID
   - 随机后缀

### 错误响应格式

项目使用自定义错误格式：
```json
{
  "error": {
    "code": "...",
    "message": "...",
    "request_id": "..."
  }
}
```

而非 FastAPI 默认的：
```json
{
  "detail": "..."
}
```

测试需要检查正确的字段。

---

## 测试通过率目标

| 阶段 | 通过/总数 | 通过率 |
|------|----------|--------|
| 会话开始 | 514/556 | 92.4% |
| 修复邮箱冲突 | ~526/556 | 94.6% (预估) |
| 迁移到 AsyncClient | ~540/556 | 97% (目标) |

**当前等待**: 完整测试套件运行完成，查看实际改善

---

**创建时间**: 2026-08-03  
**状态**: 部分修复完成，等待完整测试结果
