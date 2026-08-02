"""Job target templates for Phase 2.

Provides pre-defined job targets with competency requirements.
Users can select a template or create custom job targets from JD.
"""

from dataclasses import dataclass
from typing import Literal


JobLevel = Literal["intern", "junior", "mid", "senior", "staff"]
InterviewRound = Literal["resume", "project", "technical", "system_design", "hr"]


@dataclass
class RequirementTemplate:
    """Template for a job requirement."""
    competency_code: str
    title: str
    description: str
    importance: float  # 0.0-1.0
    expected_level: int  # 1-5
    evidence_expectation: list[str]


@dataclass
class JobTargetTemplate:
    """Pre-defined job target template."""
    template_id: str
    title: str
    level: JobLevel
    interview_round: InterviewRound
    description: str
    requirements: list[RequirementTemplate]


# ============================================================
# Backend Templates
# ============================================================

JAVA_BACKEND_ENGINEER = JobTargetTemplate(
    template_id="java_backend_mid",
    title="Java 后端工程师",
    level="mid",
    interview_round="technical",
    description="中级 Java 后端工程师，负责微服务开发和维护",
    requirements=[
        RequirementTemplate(
            competency_code="backend.language_runtime",
            title="Java 语言与 JVM",
            description="熟悉 Java 语言特性、JVM 内存模型、GC 调优",
            importance=0.9,
            expected_level=3,
            evidence_expectation=[
                "能解释 Java 并发模型（synchronized, volatile, ThreadLocal）",
                "能说明 JVM 内存分区（堆、栈、方法区）",
                "能描述常见 GC 算法及调优经验",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.api_protocol",
            title="RESTful API 设计",
            description="设计和实现 RESTful API，处理版本控制和错误响应",
            importance=0.85,
            expected_level=3,
            evidence_expectation=[
                "能设计符合 REST 原则的 API 端点",
                "能实现 API 版本控制策略",
                "能设计结构化错误响应",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.database_modeling",
            title="数据库设计与优化",
            description="MySQL/PostgreSQL schema 设计、索引优化、查询优化",
            importance=0.9,
            expected_level=3,
            evidence_expectation=[
                "能设计归一化 schema",
                "能分析和优化慢查询",
                "能使用索引提升查询性能",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.cache",
            title="Redis 缓存",
            description="使用 Redis 实现缓存方案，处理缓存一致性问题",
            importance=0.85,
            expected_level=3,
            evidence_expectation=[
                "能实现常见缓存模式（cache-aside, read-through）",
                "能处理缓存穿透、击穿、雪崩问题",
                "能设计缓存 key 和失效策略",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.message_queue",
            title="消息队列",
            description="Kafka/RabbitMQ 使用经验，处理消息可靠性",
            importance=0.75,
            expected_level=2,
            evidence_expectation=[
                "能发送和消费消息",
                "能实现重试和死信队列",
                "了解消息幂等性处理",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.transaction_consistency",
            title="事务与一致性",
            description="数据库事务、分布式事务处理经验",
            importance=0.8,
            expected_level=2,
            evidence_expectation=[
                "能使用数据库事务保证一致性",
                "了解隔离级别和死锁处理",
                "有分布式事务或补偿机制经验更佳",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.observability",
            title="可观测性",
            description="日志、监控、告警经验",
            importance=0.7,
            expected_level=2,
            evidence_expectation=[
                "能使用结构化日志记录关键信息",
                "能配置基本的监控指标和告警",
                "了解分布式追踪概念",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.testing",
            title="测试",
            description="单元测试、集成测试编写经验",
            importance=0.75,
            expected_level=2,
            evidence_expectation=[
                "能编写单元测试",
                "了解 mock/stub 使用",
                "有集成测试或 E2E 测试经验",
            ]
        ),
    ]
)


GO_BACKEND_ENGINEER = JobTargetTemplate(
    template_id="go_backend_mid",
    title="Go 后端工程师",
    level="mid",
    interview_round="technical",
    description="中级 Go 后端工程师，负责高性能服务开发",
    requirements=[
        RequirementTemplate(
            competency_code="backend.language_runtime",
            title="Go 语言与运行时",
            description="熟悉 Go 并发模型、goroutine、channel 使用",
            importance=0.95,
            expected_level=3,
            evidence_expectation=[
                "能正确使用 goroutine 和 channel",
                "能解释 Go 的调度器和 GMP 模型",
                "能处理并发竞态和死锁问题",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.api_protocol",
            title="gRPC 或 RESTful API",
            description="使用 gRPC 或 RESTful API 构建服务",
            importance=0.85,
            expected_level=3,
            evidence_expectation=[
                "能设计和实现 API 服务",
                "能使用 Protocol Buffers 定义接口",
                "能处理 API 错误和超时",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.concurrency",
            title="并发编程",
            description="高并发场景下的编程经验",
            importance=0.9,
            expected_level=3,
            evidence_expectation=[
                "能使用锁、原子操作、channel 等同步原语",
                "能设计无锁或低锁争用的并发方案",
                "能分析和解决并发 bug",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.database_modeling",
            title="数据库",
            description="关系型数据库或 NoSQL 使用经验",
            importance=0.8,
            expected_level=3,
            evidence_expectation=[
                "能设计 schema 和优化查询",
                "能使用数据库连接池",
                "了解事务和索引使用",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.cache",
            title="缓存",
            description="Redis 或其他缓存系统使用经验",
            importance=0.75,
            expected_level=2,
            evidence_expectation=[
                "能实现基本缓存逻辑",
                "了解缓存一致性问题",
                "能设计缓存失效策略",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.observability",
            title="可观测性",
            description="日志、指标、追踪",
            importance=0.7,
            expected_level=2,
            evidence_expectation=[
                "能使用结构化日志",
                "能暴露 Prometheus 指标",
                "了解分布式追踪",
            ]
        ),
    ]
)


PYTHON_BACKEND_ENGINEER = JobTargetTemplate(
    template_id="python_backend_mid",
    title="Python 后端工程师",
    level="mid",
    interview_round="technical",
    description="中级 Python 后端工程师，负责 API 服务和数据处理",
    requirements=[
        RequirementTemplate(
            competency_code="backend.language_runtime",
            title="Python 语言",
            description="熟悉 Python 语言特性、异步编程",
            importance=0.85,
            expected_level=3,
            evidence_expectation=[
                "能使用 async/await 编写异步代码",
                "了解 Python GIL 和并发限制",
                "熟悉常用标准库和框架",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.api_protocol",
            title="API 开发",
            description="使用 FastAPI/Django/Flask 开发 API",
            importance=0.9,
            expected_level=3,
            evidence_expectation=[
                "能使用 web 框架构建 RESTful API",
                "能实现请求验证和错误处理",
                "能使用 ORM 或数据库客户端",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.database_modeling",
            title="数据库",
            description="PostgreSQL/MySQL 或 MongoDB 使用经验",
            importance=0.85,
            expected_level=3,
            evidence_expectation=[
                "能设计数据库 schema",
                "能使用 ORM（SQLAlchemy/Django ORM）",
                "能优化数据库查询",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.message_queue",
            title="异步任务",
            description="Celery 或其他任务队列使用经验",
            importance=0.7,
            expected_level=2,
            evidence_expectation=[
                "能使用任务队列处理异步任务",
                "了解任务重试和错误处理",
                "能监控任务执行状态",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.testing",
            title="测试",
            description="pytest 或 unittest 测试编写",
            importance=0.75,
            expected_level=2,
            evidence_expectation=[
                "能编写单元测试和集成测试",
                "能使用 fixtures 和 mocks",
                "了解测试覆盖率",
            ]
        ),
    ]
)


AI_AGENT_ENGINEER = JobTargetTemplate(
    template_id="ai_agent_mid",
    title="AI Agent 应用工程师",
    level="mid",
    interview_round="technical",
    description="中级 AI Agent 工程师，负责 LLM 应用开发",
    requirements=[
        RequirementTemplate(
            competency_code="agent.prompt_design",
            title="Prompt 工程",
            description="设计和优化 LLM prompts",
            importance=0.95,
            expected_level=3,
            evidence_expectation=[
                "能设计结构化 prompts（system/user roles, few-shot）",
                "能使用 chain-of-thought 等高级技巧",
                "能优化 prompt 提高输出质量",
            ]
        ),
        RequirementTemplate(
            competency_code="agent.structured_output",
            title="结构化输出",
            description="使用 JSON schema 或 function calling",
            importance=0.9,
            expected_level=3,
            evidence_expectation=[
                "能使用 JSON schema 约束输出",
                "能处理解析错误和重试",
                "能使用 OpenAI function calling",
            ]
        ),
        RequirementTemplate(
            competency_code="agent.workflow_orchestration",
            title="工作流编排",
            description="LangChain/LangGraph 或类似框架使用",
            importance=0.85,
            expected_level=3,
            evidence_expectation=[
                "能构建多步骤 agent workflows",
                "能实现条件路由和循环",
                "能使用 checkpoints 保存状态",
            ]
        ),
        RequirementTemplate(
            competency_code="agent.state_management",
            title="状态管理",
            description="对话状态、记忆管理",
            importance=0.8,
            expected_level=2,
            evidence_expectation=[
                "能管理对话历史和上下文",
                "能实现状态持久化",
                "了解 context window 限制和截断策略",
            ]
        ),
        RequirementTemplate(
            competency_code="agent.tool_calling",
            title="工具集成",
            description="集成外部 API 和工具",
            importance=0.85,
            expected_level=3,
            evidence_expectation=[
                "能设计 tool schemas",
                "能处理工具调用错误和重试",
                "能实现工具认证和权限控制",
            ]
        ),
        RequirementTemplate(
            competency_code="agent.eval",
            title="评估",
            description="LLM 输出评估和测试",
            importance=0.75,
            expected_level=2,
            evidence_expectation=[
                "能创建 eval datasets",
                "能使用 LLM-as-judge 或其他评估方法",
                "能进行 A/B 测试",
            ]
        ),
        RequirementTemplate(
            competency_code="agent.cost_latency",
            title="成本与延迟优化",
            description="优化 token 使用和响应延迟",
            importance=0.7,
            expected_level=2,
            evidence_expectation=[
                "能监控 token 使用和成本",
                "能使用 prompt caching 等优化技术",
                "了解不同模型的 cost/latency/quality tradeoffs",
            ]
        ),
    ]
)


RAG_ENGINEER = JobTargetTemplate(
    template_id="rag_engineer_mid",
    title="RAG 应用工程师",
    level="mid",
    interview_round="technical",
    description="中级 RAG 工程师，负责检索增强生成系统开发",
    requirements=[
        RequirementTemplate(
            competency_code="agent.rag_fundamentals",
            title="RAG 基础",
            description="检索增强生成系统设计和实现",
            importance=0.95,
            expected_level=3,
            evidence_expectation=[
                "能使用 embeddings 实现语义检索",
                "能设计合理的文档分块策略",
                "能实现 hybrid search 或 reranking",
            ]
        ),
        RequirementTemplate(
            competency_code="agent.prompt_design",
            title="Prompt 设计",
            description="为 RAG 设计 prompts",
            importance=0.85,
            expected_level=3,
            evidence_expectation=[
                "能设计结合检索上下文的 prompts",
                "能处理检索结果不相关的情况",
                "能引导模型基于检索内容回答",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.database_modeling",
            title="向量数据库",
            description="Pinecone/Qdrant/Milvus 等向量数据库使用",
            importance=0.9,
            expected_level=3,
            evidence_expectation=[
                "能使用向量数据库存储和检索 embeddings",
                "能优化检索性能和相关性",
                "能处理索引更新和版本管理",
            ]
        ),
        RequirementTemplate(
            competency_code="agent.eval",
            title="RAG 评估",
            description="评估检索质量和生成质量",
            importance=0.8,
            expected_level=2,
            evidence_expectation=[
                "能评估检索相关性（precision/recall）",
                "能评估生成答案的准确性",
                "能分析 RAG pipeline 瓶颈",
            ]
        ),
        RequirementTemplate(
            competency_code="agent.structured_output",
            title="结构化输出",
            description="从 RAG 系统生成结构化输出",
            importance=0.7,
            expected_level=2,
            evidence_expectation=[
                "能从检索结果提取结构化信息",
                "能使用 schema 约束输出格式",
                "能处理解析错误",
            ]
        ),
    ]
)


BACKEND_INTERN = JobTargetTemplate(
    template_id="backend_intern",
    title="后端实习生",
    level="intern",
    interview_round="resume",
    description="后端实习生，了解基本的 web 开发和数据库知识",
    requirements=[
        RequirementTemplate(
            competency_code="backend.language_runtime",
            title="编程语言",
            description="熟悉至少一门后端语言（Java/Python/Go）",
            importance=0.85,
            expected_level=2,
            evidence_expectation=[
                "能编写基本的程序逻辑",
                "了解面向对象或函数式编程",
                "能使用标准库完成常见任务",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.api_protocol",
            title="API 基础",
            description="了解 HTTP 协议和 RESTful API 概念",
            importance=0.75,
            expected_level=2,
            evidence_expectation=[
                "了解 HTTP 方法和状态码",
                "能调用和测试 API",
                "了解 JSON 格式",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.database_modeling",
            title="数据库基础",
            description="了解关系型数据库和 SQL",
            importance=0.8,
            expected_level=2,
            evidence_expectation=[
                "能编写基本的 SQL 查询",
                "了解表、主键、外键概念",
                "能使用数据库客户端或 ORM",
            ]
        ),
        RequirementTemplate(
            competency_code="backend.testing",
            title="测试基础",
            description="了解单元测试概念",
            importance=0.6,
            expected_level=1,
            evidence_expectation=[
                "了解测试的重要性",
                "能编写简单的单元测试",
                "了解测试框架基本使用",
            ]
        ),
    ]
)


# ============================================================
# Template Registry
# ============================================================

ALL_TEMPLATES = [
    JAVA_BACKEND_ENGINEER,
    GO_BACKEND_ENGINEER,
    PYTHON_BACKEND_ENGINEER,
    AI_AGENT_ENGINEER,
    RAG_ENGINEER,
    BACKEND_INTERN,
]


def get_template_by_id(template_id: str) -> JobTargetTemplate | None:
    """Get template by ID."""
    for template in ALL_TEMPLATES:
        if template.template_id == template_id:
            return template
    return None


def list_templates(level: JobLevel | None = None) -> list[JobTargetTemplate]:
    """List all templates, optionally filtered by level."""
    if level is None:
        return ALL_TEMPLATES
    return [t for t in ALL_TEMPLATES if t.level == level]


def get_template_ids() -> list[str]:
    """Get list of all template IDs."""
    return [t.template_id for t in ALL_TEMPLATES]
