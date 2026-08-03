# 测试基础设施修复总结

**日期**: 2026-08-03  
**任务**: 修复异步测试 event loop 问题

---

## 问题诊断

### 问题 1: Event Loop Closed 错误

**症状**:
```
RuntimeError: Event loop is closed
```

**根本原因**:
- `PromptRegistry` 和 `RubricRegistry` 使用全局 `async_session_factory()` 创建数据库会话
- 测试 fixture 创建的是内存 SQLite 数据库，但每个新连接都会创建独立的内存数据库
- Registry 创建的 session 连接到一个新的空数据库（没有表），导致查询失败

**影响测试**:
- `tests/test_prompt_registry.py`: 8/9 测试失败
- `tests/test_rubric_versioning.py`: 9/10 测试失败

---

## 解决方案

### 1. 添加 Session Factory 参数支持

**修改文件**: `app/evals/prompt_registry.py`, `app/evals/rubric_versioning.py`

两个类都已经支持 `session_factory` 参数（在 `__init__` 中）：
```python
class PromptRegistry:
    def __init__(self, session_factory=None):
        self._cache: dict[tuple[str, int], PromptSpec] = {}
        self._session_factory = session_factory or async_session_factory
```

### 2. 修复测试 Fixture

**修改文件**: `tests/test_prompt_registry.py`, `tests/test_rubric_versioning.py`

将测试 fixture 改为直接使用 `async_engine` 创建 session factory：

```python
@pytest.fixture
async def registry(async_engine):
    """Create a fresh registry for each test with test database session."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    return PromptRegistry(session_factory=session_factory)
```

### 3. 使用临时文件数据库

**修改文件**: `tests/conftest.py`

**关键变更**:
- 从内存数据库 `sqlite+aiosqlite:///:memory:` 改为临时文件数据库
- 使用 `tempfile.mkstemp()` 创建临时文件
- 测试后清理临时文件

**原因**:
- SQLite 内存数据库 (`:memory:`) 在每个连接中都是独立的
- 即使使用 `cache=shared` 也无法在 aiosqlite 中正常工作
- 临时文件数据库确保所有连接访问同一个数据库

```python
@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async engine for tests with temporary file database."""
    # Create a temporary database file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    TEST_DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()
    os.unlink(db_path)
```

### 4. 确保所有模型被导入

**修改文件**: `tests/conftest.py`

添加显式导入确保所有模型注册到 `Base.metadata`：
```python
from app.persistence.models import (
    User, ResumeSource, ResumeRevision, ..., PromptVersion, RubricVersion,
    ClaimCompetencyMapping, ClaimRequirementMapping,
)
```

### 5. 安装缺失的依赖

**问题**: `ModuleNotFoundError: No module named 'aiosqlite'`

**解决**:
```bash
pip install aiosqlite
```

已在 `pyproject.toml` 中添加到 dev 依赖。

---

## 测试结果

### 修复前
- `test_prompt_registry.py`: 1 passed, 8 failed
- `test_rubric_versioning.py`: 1 passed, 9 failed
- **总计**: 2 passed, 17 failed

### 修复后
- `test_prompt_registry.py`: 9 passed ✅
- `test_rubric_versioning.py`: 11 passed ✅
- **总计**: 20 passed, 0 failed 🎉

---

## 关键经验

1. **SQLite 内存数据库的陷阱**
   - 每个连接都是独立的内存数据库
   - `cache=shared` 在某些驱动中不可靠
   - 对于需要多连接的测试，使用临时文件数据库

2. **依赖注入的重要性**
   - Registry 类支持 `session_factory` 参数使测试成为可能
   - 避免硬编码全局依赖

3. **模型注册**
   - SQLAlchemy 需要显式导入模型才能注册到 `Base.metadata`
   - 在 `conftest.py` 中集中导入所有模型

4. **Fixture 作用域**
   - 使用 `scope="function"` 确保每个测试有干净的数据库
   - 临时文件在测试后正确清理

---

## 后续工作

- ✅ Prompt/Rubric registry 测试修复完成
- 🔜 修复 E2E 测试客户端问题 (TestClient → AsyncClient)
- 🔜 修复集成测试数据库连接问题 (auth, data_deletion)
- 🔜 目标: 测试通过率从 85.8% 提升到 95%+

---

**修复时间**: 约 1 小时  
**修复测试数**: 20 个测试  
**影响**: 解除了 prompt 和 rubric 版本控制测试的阻塞
