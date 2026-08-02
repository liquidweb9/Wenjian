"""Competency catalog for Phase 2.

Defines the structured competencies used for:
- Job requirement extraction
- Claim-to-competency mapping
- Interview planning
- Ability profile tracking

Phase 2 focuses on backend and AI agent engineering competencies only.
"""

from dataclasses import dataclass
from typing import Literal


CompetencyDomain = Literal["backend", "agent"]


@dataclass
class LevelDescriptor:
    """Behavioral description for a competency level."""
    level: int  # 1-5
    title: str
    behavior: str  # Observable behavior at this level


@dataclass
class CompetencyDefinition:
    """Full definition of a competency."""
    code: str  # Unique identifier (e.g., "backend.cache")
    domain: CompetencyDomain
    title: str
    description: str
    levels: list[LevelDescriptor]


# ============================================================
# Backend Engineering Competencies
# ============================================================

BACKEND_COMPETENCIES = [
    CompetencyDefinition(
        code="backend.language_runtime",
        domain="backend",
        title="Language & Runtime",
        description="Understanding of target language(s) and runtime environment",
        levels=[
            LevelDescriptor(1, "Basic syntax", "Can write simple programs, understand basic syntax"),
            LevelDescriptor(2, "Standard library", "Uses standard library effectively, understands common patterns"),
            LevelDescriptor(3, "Concurrency & memory", "Understands concurrency primitives, memory management, GC behavior"),
            LevelDescriptor(4, "Performance tuning", "Profiles and optimizes runtime performance, understands JVM/GC tuning"),
            LevelDescriptor(5, "Runtime internals", "Deep knowledge of runtime internals, can contribute to runtime/compiler"),
        ]
    ),

    CompetencyDefinition(
        code="backend.api_protocol",
        domain="backend",
        title="API & Protocol Design",
        description="RESTful APIs, gRPC, GraphQL design and implementation",
        levels=[
            LevelDescriptor(1, "Basic HTTP", "Understands HTTP methods, status codes, headers"),
            LevelDescriptor(2, "REST principles", "Designs RESTful endpoints, proper resource modeling"),
            LevelDescriptor(3, "Versioning & errors", "Implements API versioning, structured error responses, pagination"),
            LevelDescriptor(4, "Protocol selection", "Chooses appropriate protocol (REST/gRPC/GraphQL), designs schemas"),
            LevelDescriptor(5, "API platform", "Designs API gateways, rate limiting, documentation systems"),
        ]
    ),

    CompetencyDefinition(
        code="backend.database_modeling",
        domain="backend",
        title="Database Modeling",
        description="Schema design, query optimization, indexes",
        levels=[
            LevelDescriptor(1, "Basic SQL", "Writes simple SELECT/INSERT/UPDATE queries"),
            LevelDescriptor(2, "Schema design", "Designs normalized schemas, understands foreign keys and joins"),
            LevelDescriptor(3, "Query optimization", "Uses indexes effectively, analyzes query plans, optimizes N+1 queries"),
            LevelDescriptor(4, "Advanced modeling", "Designs for denormalization, partitioning, read replicas"),
            LevelDescriptor(5, "Database architecture", "Designs sharding strategies, migration plans, multi-region consistency"),
        ]
    ),

    CompetencyDefinition(
        code="backend.transaction_consistency",
        domain="backend",
        title="Transactions & Consistency",
        description="ACID transactions, distributed transactions, consistency patterns",
        levels=[
            LevelDescriptor(1, "Basic transactions", "Uses database transactions for single operations"),
            LevelDescriptor(2, "Isolation levels", "Understands isolation levels, handles deadlocks"),
            LevelDescriptor(3, "Distributed transactions", "Implements 2PC or Saga pattern, handles compensation"),
            LevelDescriptor(4, "Consistency patterns", "Chooses between strong/eventual consistency, implements idempotency"),
            LevelDescriptor(5, "Consistency architecture", "Designs multi-service consistency, conflict resolution strategies"),
        ]
    ),

    CompetencyDefinition(
        code="backend.cache",
        domain="backend",
        title="Caching",
        description="Cache strategies, invalidation, distributed caching",
        levels=[
            LevelDescriptor(1, "Basic caching", "Uses in-memory cache for simple data"),
            LevelDescriptor(2, "Cache patterns", "Implements cache-aside, read-through, write-through patterns"),
            LevelDescriptor(3, "Invalidation & consistency", "Handles cache invalidation, stampede prevention, TTL strategies"),
            LevelDescriptor(4, "Distributed caching", "Designs Redis clusters, handles cache warming, monitors hit rates"),
            LevelDescriptor(5, "Cache architecture", "Designs multi-layer caching, CDN integration, cost-performance tradeoffs"),
        ]
    ),

    CompetencyDefinition(
        code="backend.message_queue",
        domain="backend",
        title="Message Queues",
        description="Async messaging, event-driven architecture, queue reliability",
        levels=[
            LevelDescriptor(1, "Basic queues", "Publishes and consumes messages from a queue"),
            LevelDescriptor(2, "Reliability patterns", "Implements retry, dead-letter queues, at-least-once delivery"),
            LevelDescriptor(3, "Event design", "Designs event schemas, topic/exchange routing, consumer groups"),
            LevelDescriptor(4, "Production operations", "Monitors lag, handles backpressure, implements poison message handling"),
            LevelDescriptor(5, "Messaging architecture", "Designs event-driven systems, CQRS, event sourcing, saga orchestration"),
        ]
    ),

    CompetencyDefinition(
        code="backend.concurrency",
        domain="backend",
        title="Concurrency & Parallelism",
        description="Multi-threading, async I/O, race conditions, locks",
        levels=[
            LevelDescriptor(1, "Basic threading", "Understands threads vs processes, can spawn threads"),
            LevelDescriptor(2, "Synchronization", "Uses locks, semaphores, understands race conditions"),
            LevelDescriptor(3, "Async patterns", "Implements async/await, non-blocking I/O, thread pools"),
            LevelDescriptor(4, "Lock-free programming", "Uses atomic operations, understands memory ordering, avoids deadlocks"),
            LevelDescriptor(5, "Concurrency architecture", "Designs actor systems, work-stealing schedulers, high-concurrency services"),
        ]
    ),

    CompetencyDefinition(
        code="backend.observability",
        domain="backend",
        title="Observability",
        description="Logging, metrics, tracing, alerting",
        levels=[
            LevelDescriptor(1, "Basic logging", "Adds log statements, understands log levels"),
            LevelDescriptor(2, "Structured logging", "Uses structured logs, log sampling, log aggregation"),
            LevelDescriptor(3, "Metrics & tracing", "Implements metrics (RED/USE), distributed tracing, SLIs"),
            LevelDescriptor(4, "Alerting & dashboards", "Designs alerts, SLOs, on-call runbooks, correlation"),
            LevelDescriptor(5, "Observability platform", "Designs org-wide observability, cost optimization, anomaly detection"),
        ]
    ),

    CompetencyDefinition(
        code="backend.failure_recovery",
        domain="backend",
        title="Failure Handling & Recovery",
        description="Error handling, retries, circuit breakers, graceful degradation",
        levels=[
            LevelDescriptor(1, "Basic error handling", "Uses try-catch, returns error codes"),
            LevelDescriptor(2, "Retry patterns", "Implements exponential backoff, timeout handling"),
            LevelDescriptor(3, "Circuit breakers", "Implements circuit breakers, fallbacks, graceful degradation"),
            LevelDescriptor(4, "Failure scenarios", "Designs for partial failures, handles cascading failures, bulkheads"),
            LevelDescriptor(5, "Resilience architecture", "Designs chaos engineering, multi-region failover, disaster recovery"),
        ]
    ),

    CompetencyDefinition(
        code="backend.security",
        domain="backend",
        title="Security",
        description="Authentication, authorization, input validation, secrets management",
        levels=[
            LevelDescriptor(1, "Basic auth", "Implements password hashing, simple login"),
            LevelDescriptor(2, "Auth patterns", "Implements JWT, OAuth2, session management"),
            LevelDescriptor(3, "Authorization", "Designs RBAC/ABAC, input validation, OWASP Top 10 awareness"),
            LevelDescriptor(4, "Secrets & compliance", "Manages secrets rotation, implements audit logs, GDPR compliance"),
            LevelDescriptor(5, "Security architecture", "Designs zero-trust systems, threat modeling, security reviews"),
        ]
    ),

    CompetencyDefinition(
        code="backend.system_design",
        domain="backend",
        title="System Design",
        description="Architecture, scalability, tradeoffs, capacity planning",
        levels=[
            LevelDescriptor(1, "Basic architecture", "Understands client-server, database, API layers"),
            LevelDescriptor(2, "Service boundaries", "Designs microservices, understands service coupling"),
            LevelDescriptor(3, "Scalability patterns", "Designs for horizontal scaling, load balancing, stateless services"),
            LevelDescriptor(4, "Complex systems", "Designs multi-region systems, handles CAP theorem tradeoffs, capacity planning"),
            LevelDescriptor(5, "Platform architecture", "Designs platforms, infrastructure abstractions, org-wide technical strategy"),
        ]
    ),

    CompetencyDefinition(
        code="backend.testing",
        domain="backend",
        title="Testing",
        description="Unit tests, integration tests, E2E tests, test design",
        levels=[
            LevelDescriptor(1, "Basic unit tests", "Writes simple unit tests, understands assertions"),
            LevelDescriptor(2, "Test patterns", "Uses mocks/stubs, tests edge cases, understands coverage"),
            LevelDescriptor(3, "Integration testing", "Writes integration tests, uses test databases, contract testing"),
            LevelDescriptor(4, "Test strategy", "Designs test pyramid, property-based testing, performance testing"),
            LevelDescriptor(5, "Testing platform", "Designs CI/CD pipelines, test infrastructure, flaky test detection"),
        ]
    ),

    CompetencyDefinition(
        code="backend.delivery",
        domain="backend",
        title="Deployment & Delivery",
        description="CI/CD, containerization, infrastructure as code",
        levels=[
            LevelDescriptor(1, "Basic deployment", "Deploys applications manually, understands release process"),
            LevelDescriptor(2, "CI/CD basics", "Uses CI/CD pipelines, containerizes applications"),
            LevelDescriptor(3, "Infrastructure as code", "Uses Terraform/CloudFormation, implements blue-green deployments"),
            LevelDescriptor(4, "Advanced delivery", "Implements canary deployments, feature flags, rollback strategies"),
            LevelDescriptor(5, "Platform delivery", "Designs deployment platforms, multi-region orchestration, progressive delivery"),
        ]
    ),
]


# ============================================================
# AI Agent Engineering Competencies
# ============================================================

AGENT_COMPETENCIES = [
    CompetencyDefinition(
        code="agent.prompt_design",
        domain="agent",
        title="Prompt Engineering",
        description="Prompt design, few-shot learning, prompt optimization",
        levels=[
            LevelDescriptor(1, "Basic prompts", "Writes simple prompts, understands temperature/top-p"),
            LevelDescriptor(2, "Structured prompts", "Uses system/user roles, few-shot examples, formats outputs"),
            LevelDescriptor(3, "Advanced techniques", "Implements chain-of-thought, prompt decomposition, error handling"),
            LevelDescriptor(4, "Optimization", "A/B tests prompts, uses eval datasets, optimizes cost/latency"),
            LevelDescriptor(5, "Prompt platform", "Designs prompt registries, versioning, multi-model strategies"),
        ]
    ),

    CompetencyDefinition(
        code="agent.structured_output",
        domain="agent",
        title="Structured Output",
        description="JSON schemas, function calling, output validation",
        levels=[
            LevelDescriptor(1, "Basic parsing", "Parses JSON from LLM outputs"),
            LevelDescriptor(2, "Schema validation", "Uses JSON schema, handles parse errors, retry logic"),
            LevelDescriptor(3, "Function calling", "Implements OpenAI function calling, structured extraction"),
            LevelDescriptor(4, "Complex schemas", "Designs nested schemas, union types, validation with retries"),
            LevelDescriptor(5, "Schema platform", "Designs schema evolution, backward compatibility, multi-model schemas"),
        ]
    ),

    CompetencyDefinition(
        code="agent.workflow_orchestration",
        domain="agent",
        title="Workflow Orchestration",
        description="Agent graphs, state machines, multi-agent systems",
        levels=[
            LevelDescriptor(1, "Sequential flow", "Implements simple sequential agent workflows"),
            LevelDescriptor(2, "Conditional routing", "Implements conditional branching, loops, retries"),
            LevelDescriptor(3, "State management", "Uses LangGraph/stateful workflows, implements checkpoints"),
            LevelDescriptor(4, "Multi-agent", "Designs multi-agent coordination, supervisor patterns"),
            LevelDescriptor(5, "Agent platform", "Designs agent orchestration platforms, workflow DSLs"),
        ]
    ),

    CompetencyDefinition(
        code="agent.state_management",
        domain="agent",
        title="State Management",
        description="Conversation state, memory, persistence, recovery",
        levels=[
            LevelDescriptor(1, "Basic state", "Tracks conversation history in memory"),
            LevelDescriptor(2, "Persistence", "Persists state to database, implements checkpointing"),
            LevelDescriptor(3, "Memory patterns", "Implements short-term/long-term memory, context summarization"),
            LevelDescriptor(4, "Recovery", "Implements crash recovery, idempotency, distributed state"),
            LevelDescriptor(5, "State platform", "Designs state synchronization, multi-user state, CRDT-based state"),
        ]
    ),

    CompetencyDefinition(
        code="agent.tool_calling",
        domain="agent",
        title="Tool Use & Integration",
        description="Function calling, API integration, tool reliability",
        levels=[
            LevelDescriptor(1, "Basic tools", "Integrates simple API calls as tools"),
            LevelDescriptor(2, "Tool schemas", "Designs tool schemas, handles tool errors"),
            LevelDescriptor(3, "Reliability", "Implements tool retry, timeout, fallback, rate limiting"),
            LevelDescriptor(4, "Advanced tools", "Designs tool composition, parallel tool calling, tool authentication"),
            LevelDescriptor(5, "Tool platform", "Designs tool registries, sandboxed execution, tool marketplace"),
        ]
    ),

    CompetencyDefinition(
        code="agent.rag_fundamentals",
        domain="agent",
        title="RAG Fundamentals",
        description="Retrieval-augmented generation, embeddings, vector search",
        levels=[
            LevelDescriptor(1, "Basic RAG", "Implements simple keyword-based retrieval + generation"),
            LevelDescriptor(2, "Embeddings", "Uses embeddings for semantic search, understands chunking strategies"),
            LevelDescriptor(3, "Advanced retrieval", "Implements hybrid search, reranking, query expansion"),
            LevelDescriptor(4, "Production RAG", "Optimizes retrieval latency, handles index updates, monitors relevance"),
            LevelDescriptor(5, "RAG platform", "Designs multi-source RAG, knowledge graph integration, adaptive retrieval"),
        ]
    ),

    CompetencyDefinition(
        code="agent.eval",
        domain="agent",
        title="Evaluation",
        description="LLM evaluation, metrics, regression testing, human eval",
        levels=[
            LevelDescriptor(1, "Manual testing", "Tests LLM outputs manually"),
            LevelDescriptor(2, "Eval datasets", "Creates eval datasets, compares outputs"),
            LevelDescriptor(3, "Automated metrics", "Implements LLM-as-judge, BLEU/ROUGE, regression tests"),
            LevelDescriptor(4, "Production evals", "Designs A/B testing, shadow mode, online metrics"),
            LevelDescriptor(5, "Eval platform", "Designs org-wide eval infrastructure, human-in-the-loop eval"),
        ]
    ),

    CompetencyDefinition(
        code="agent.guardrail",
        domain="agent",
        title="Guardrails & Safety",
        description="Content filtering, jailbreak prevention, PII protection",
        levels=[
            LevelDescriptor(1, "Basic filtering", "Implements simple keyword-based content filtering"),
            LevelDescriptor(2, "Moderation APIs", "Uses moderation APIs, handles toxic outputs"),
            LevelDescriptor(3, "Input validation", "Implements prompt injection detection, PII scrubbing"),
            LevelDescriptor(4, "Advanced safety", "Designs jailbreak prevention, adversarial testing, output validation"),
            LevelDescriptor(5, "Safety platform", "Designs org-wide safety frameworks, compliance automation"),
        ]
    ),

    CompetencyDefinition(
        code="agent.cost_latency",
        domain="agent",
        title="Cost & Latency Optimization",
        description="Token optimization, caching, model selection, streaming",
        levels=[
            LevelDescriptor(1, "Basic awareness", "Understands token costs, monitors usage"),
            LevelDescriptor(2, "Optimization", "Implements prompt caching, truncation, batch processing"),
            LevelDescriptor(3, "Model selection", "Chooses models based on cost/latency/quality tradeoffs"),
            LevelDescriptor(4, "Advanced optimization", "Implements semantic caching, speculative decoding, streaming"),
            LevelDescriptor(5, "Cost platform", "Designs cost attribution, budgets, multi-model routing, FinOps"),
        ]
    ),

    CompetencyDefinition(
        code="agent.production_reliability",
        domain="agent",
        title="Production Reliability",
        description="Error handling, retries, monitoring, SLAs",
        levels=[
            LevelDescriptor(1, "Basic error handling", "Handles API errors, implements retries"),
            LevelDescriptor(2, "Graceful degradation", "Implements fallback models, timeout handling"),
            LevelDescriptor(3, "Monitoring", "Implements latency/error/cost metrics, alerting"),
            LevelDescriptor(4, "SLAs", "Designs SLOs for agent systems, implements circuit breakers"),
            LevelDescriptor(5, "Platform reliability", "Designs multi-region agents, chaos engineering for LLMs"),
        ]
    ),
]


# ============================================================
# Catalog Access
# ============================================================

ALL_COMPETENCIES = BACKEND_COMPETENCIES + AGENT_COMPETENCIES


def get_competency_by_code(code: str) -> CompetencyDefinition | None:
    """Get competency definition by code."""
    for comp in ALL_COMPETENCIES:
        if comp.code == code:
            return comp
    return None


def get_competencies_by_domain(domain: CompetencyDomain) -> list[CompetencyDefinition]:
    """Get all competencies in a domain."""
    return [comp for comp in ALL_COMPETENCIES if comp.domain == domain]


def get_all_competency_codes() -> list[str]:
    """Get list of all competency codes."""
    return [comp.code for comp in ALL_COMPETENCIES]
