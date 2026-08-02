"""Claim Mapper for Phase 2.

Maps resume claims to competencies and job requirements.
Uses rule-based heuristics + optional LLM assistance.
"""

from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field

from app.competencies import get_competency_by_code, get_all_competency_codes


# ============================================================
# Schemas
# ============================================================

class CompetencyMapping(BaseModel):
    """Mapping from a claim to a competency."""
    claim_id: str
    competency_code: str
    mapping_strength: float = Field(ge=0.0, le=1.0, description="Confidence 0.0-1.0")
    mapping_reason: str = Field(description="Why this competency matches the claim")


class RequirementMapping(BaseModel):
    """Mapping from a claim to a job requirement."""
    claim_id: str
    requirement_id: str
    competency_code: str
    relevance: float = Field(ge=0.0, le=1.0, description="How relevant the claim is to this requirement")
    coverage_level: int = Field(ge=0, le=5, description="Estimated level covered by claim (0=none, 1-5=levels)")
    mapping_reason: str = Field(description="Why this requirement matches the claim")


class ClaimMappingResult(BaseModel):
    """Result of mapping a single claim."""
    claim_id: str
    claim_text: str
    competency_mappings: list[CompetencyMapping]
    requirement_mappings: list[RequirementMapping]


# ============================================================
# LLM Gateway Protocol (optional, for future LLM-assisted mapping)
# ============================================================

class LLMGateway(Protocol):
    """Protocol for optional LLM-assisted mapping."""

    async def generate_structured(
        self,
        task_name: str,
        prompt: str,
        output_model: type[BaseModel],
        **kwargs
    ) -> BaseModel:
        """Generate structured output from LLM."""
        ...


# ============================================================
# Claim Mapper
# ============================================================

@dataclass
class ClaimMapper:
    """Maps resume claims to competencies and job requirements.

    Current implementation uses rule-based keyword matching.
    Future versions can add LLM assistance for ambiguous cases.
    """

    llm: LLMGateway | None = None
    use_llm_fallback: bool = False

    # Keyword patterns for competency matching
    COMPETENCY_KEYWORDS = {
        "backend.language_runtime": [
            "java", "jvm", "go", "golang", "python", "node.js", "javascript",
            "rust", "garbage collection", "gc", "memory management", "并发模型"
        ],
        "backend.api_protocol": [
            "rest", "restful", "grpc", "graphql", "api", "http", "rpc",
            "websocket", "protobuf", "openapi", "swagger"
        ],
        "backend.database_modeling": [
            "mysql", "postgresql", "postgres", "database", "sql", "schema",
            "index", "索引", "query", "orm", "数据库", "表设计", "归一化"
        ],
        "backend.transaction_consistency": [
            "transaction", "事务", "acid", "consistency", "一致性", "isolation",
            "distributed transaction", "2pc", "saga", "tcc"
        ],
        "backend.cache": [
            "redis", "cache", "缓存", "memcached", "cdn", "cache-aside",
            "缓存穿透", "缓存击穿", "缓存雪崩", "失效策略"
        ],
        "backend.message_queue": [
            "kafka", "rabbitmq", "mq", "message queue", "消息队列", "pulsar",
            "event stream", "pub/sub", "订阅", "发布"
        ],
        "backend.concurrency": [
            "concurrency", "并发", "goroutine", "async", "thread", "线程",
            "lock", "mutex", "channel", "race condition", "deadlock"
        ],
        "backend.observability": [
            "log", "日志", "metric", "监控", "trace", "tracing", "prometheus",
            "grafana", "elk", "observability", "可观测性", "alert", "告警"
        ],
        "backend.failure_recovery": [
            "retry", "重试", "circuit breaker", "熔断", "rate limit", "限流",
            "failover", "高可用", "disaster recovery", "容灾"
        ],
        "backend.security": [
            "security", "安全", "authentication", "认证", "authorization", "授权",
            "encryption", "加密", "jwt", "oauth", "xss", "sql injection"
        ],
        "backend.system_design": [
            "architecture", "架构", "microservice", "微服务", "design pattern",
            "设计模式", "scalability", "扩展性", "高并发", "distributed system"
        ],
        "backend.testing": [
            "test", "测试", "unit test", "integration test", "mock", "jest",
            "pytest", "coverage", "覆盖率", "ci", "continuous integration"
        ],
        "backend.delivery": [
            "docker", "kubernetes", "k8s", "ci/cd", "deployment", "部署",
            "jenkins", "github actions", "pipeline", "容器", "helm"
        ],
        "agent.prompt_design": [
            "prompt", "few-shot", "chain-of-thought", "cot", "system message",
            "temperature", "提示词", "指令优化"
        ],
        "agent.structured_output": [
            "json", "schema", "pydantic", "structured output", "function calling",
            "tool use", "格式化输出", "schema validation"
        ],
        "agent.workflow_orchestration": [
            "langgraph", "workflow", "state machine", "orchestration", "编排",
            "agent loop", "multi-agent", "流程控制"
        ],
        "agent.state_management": [
            "state", "checkpoint", "状态管理", "persistence", "持久化",
            "resume", "恢复", "interrupt", "中断"
        ],
        "agent.tool_calling": [
            "tool", "function calling", "工具调用", "plugin", "api integration",
            "external service", "tool use"
        ],
        "agent.rag_fundamentals": [
            "rag", "retrieval", "embedding", "向量", "vector", "similarity",
            "semantic search", "检索增强", "知识库"
        ],
        "agent.eval": [
            "eval", "evaluation", "benchmark", "测试集", "golden dataset",
            "regression", "回归测试", "metric", "accuracy"
        ],
        "agent.guardrail": [
            "guardrail", "safety", "安全", "moderation", "content filter",
            "prompt injection", "jailbreak", "adversarial"
        ],
        "agent.cost_latency": [
            "cost", "成本", "latency", "延迟", "token", "optimization",
            "优化", "caching", "streaming", "batch"
        ],
        "agent.production_reliability": [
            "production", "生产环境", "monitoring", "监控", "error handling",
            "retry", "fallback", "reliability", "可靠性"
        ],
    }

    def _calculate_keyword_match_score(self, text: str, keywords: list[str]) -> float:
        """Calculate keyword match score for a text.

        Returns:
            Score 0.0-1.0 based on keyword coverage
        """
        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)

        if matches == 0:
            return 0.0

        # Scoring formula:
        # 1 match: 0.6, 2 matches: 0.75, 3+ matches: 0.9
        if matches == 1:
            return 0.6
        elif matches == 2:
            return 0.75
        else:
            return 0.9

    def map_claim_to_competencies(
        self,
        claim_id: str,
        claim_text: str,
        min_strength: float = 0.5,
    ) -> list[CompetencyMapping]:
        """Map a claim to relevant competencies.

        Args:
            claim_id: Claim identifier
            claim_text: Claim text content
            min_strength: Minimum mapping strength to include (default 0.5)

        Returns:
            List of competency mappings sorted by strength (descending)
        """
        mappings = []

        for comp_code, keywords in self.COMPETENCY_KEYWORDS.items():
            score = self._calculate_keyword_match_score(claim_text, keywords)

            if score >= min_strength:
                # Generate reason based on matched keywords
                matched_kws = [kw for kw in keywords if kw.lower() in claim_text.lower()]
                reason = f"Claim mentions: {', '.join(matched_kws[:3])}"

                mappings.append(CompetencyMapping(
                    claim_id=claim_id,
                    competency_code=comp_code,
                    mapping_strength=score,
                    mapping_reason=reason,
                ))

        # Sort by strength (descending)
        mappings.sort(key=lambda m: m.mapping_strength, reverse=True)

        return mappings

    def map_claim_to_requirements(
        self,
        claim_id: str,
        claim_text: str,
        requirements: list[dict],  # List of {requirement_id, competency_code, title, importance, expected_level}
        competency_mappings: list[CompetencyMapping],
        min_relevance: float = 0.4,
    ) -> list[RequirementMapping]:
        """Map a claim to job requirements.

        Args:
            claim_id: Claim identifier
            claim_text: Claim text content
            requirements: List of job requirements (from JobTarget)
            competency_mappings: Already-computed competency mappings for this claim
            min_relevance: Minimum relevance to include (default 0.4)

        Returns:
            List of requirement mappings sorted by relevance (descending)
        """
        # Build competency_code → mapping_strength lookup
        comp_strength = {
            m.competency_code: m.mapping_strength
            for m in competency_mappings
        }

        mappings = []

        for req in requirements:
            req_id = req["requirement_id"]
            comp_code = req["competency_code"]
            req_title = req.get("title", "")
            req_importance = req.get("importance", 0.8)
            req_level = req.get("expected_level", 3)

            # Base relevance from competency mapping
            base_relevance = comp_strength.get(comp_code, 0.0)

            if base_relevance == 0.0:
                continue  # No competency match

            # Boost relevance if requirement title also appears in claim
            title_boost = 0.0
            if req_title and req_title.lower() in claim_text.lower():
                title_boost = 0.15

            relevance = min(1.0, base_relevance + title_boost)

            if relevance < min_relevance:
                continue

            # Estimate coverage level (conservative)
            # For now, assume claim provides evidence for level 2-3
            # (user has done it, but depth unknown until interview)
            coverage_level = 2 if relevance >= 0.7 else 1

            reason = f"Matches competency {comp_code} (strength {base_relevance:.2f})"
            if title_boost > 0:
                reason += f", title keyword match"

            mappings.append(RequirementMapping(
                claim_id=claim_id,
                requirement_id=req_id,
                competency_code=comp_code,
                relevance=relevance,
                coverage_level=coverage_level,
                mapping_reason=reason,
            ))

        # Sort by relevance (descending)
        mappings.sort(key=lambda m: m.relevance, reverse=True)

        return mappings

    def map_claim(
        self,
        claim_id: str,
        claim_text: str,
        requirements: list[dict] | None = None,
        min_competency_strength: float = 0.5,
        min_requirement_relevance: float = 0.4,
    ) -> ClaimMappingResult:
        """Map a claim to both competencies and requirements.

        Args:
            claim_id: Claim identifier
            claim_text: Claim text content
            requirements: Optional list of job requirements (for requirement mapping)
            min_competency_strength: Min strength for competency mapping
            min_requirement_relevance: Min relevance for requirement mapping

        Returns:
            Complete mapping result
        """
        # Map to competencies first
        comp_mappings = self.map_claim_to_competencies(
            claim_id=claim_id,
            claim_text=claim_text,
            min_strength=min_competency_strength,
        )

        # Map to requirements (if provided)
        req_mappings = []
        if requirements:
            req_mappings = self.map_claim_to_requirements(
                claim_id=claim_id,
                claim_text=claim_text,
                requirements=requirements,
                competency_mappings=comp_mappings,
                min_relevance=min_requirement_relevance,
            )

        return ClaimMappingResult(
            claim_id=claim_id,
            claim_text=claim_text,
            competency_mappings=comp_mappings,
            requirement_mappings=req_mappings,
        )
