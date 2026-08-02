"""JD (Job Description) Parser for Phase 2.

Extracts structured requirements from raw JD text using LLM.
"""

from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field

from app.competencies import get_competency_by_code, get_all_competency_codes


# ============================================================
# Schemas
# ============================================================

class SourceSpan(BaseModel):
    """Tracks where in the JD text this requirement came from."""
    start: int
    end: int
    text: str


class ParsedRequirement(BaseModel):
    """Structured requirement parsed from JD."""
    competency_code: str = Field(description="Competency code from catalog (e.g., 'backend.cache')")
    title: str = Field(description="Short title for this requirement")
    description: str = Field(description="Detailed description of what's required")
    importance: float = Field(ge=0.0, le=1.0, description="Importance score 0.0-1.0")
    expected_level: int = Field(ge=1, le=5, description="Expected proficiency level 1-5")
    evidence_expectation: list[str] = Field(
        min_length=2,
        description="List of specific evidence points to verify"
    )
    source_span: SourceSpan | None = Field(
        default=None,
        description="Link back to JD text (optional)"
    )


class JDParseResult(BaseModel):
    """Result of JD parsing."""
    requirements: list[ParsedRequirement]
    inferred_level: str | None = Field(
        default=None,
        description="Inferred job level (intern/junior/mid/senior/staff)"
    )
    inferred_round: str | None = Field(
        default=None,
        description="Inferred interview round (resume/project/technical/system_design)"
    )


# ============================================================
# LLM Gateway Protocol
# ============================================================

class LLMGateway(Protocol):
    """Protocol for LLM calls (can be mocked in tests)."""

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
# JD Parser
# ============================================================

@dataclass
class JDParser:
    """Parser for extracting structured requirements from JD text."""

    llm: LLMGateway
    prompt_version: str = "v1.0"

    def _build_prompt(self, jd_text: str) -> str:
        """Build prompt for JD parsing."""
        competency_list = "\n".join([
            f"- {code}: {get_competency_by_code(code).title if get_competency_by_code(code) else code}"
            for code in get_all_competency_codes()
        ])

        return f"""你是一个岗位描述（JD）分析专家。请从以下 JD 文本中提取结构化的能力要求。

可用的能力代码列表：
{competency_list}

JD 文本：
```
{jd_text}
```

提取规则：
1. **Competency Code**: 必须从上述能力代码列表中选择最匹配的。如果 JD 提到"Redis缓存"，应选择 "backend.cache"。
2. **Title**: 简短标题，描述这个要求（如"Redis 缓存设计"）
3. **Description**: 详细描述这个要求的具体内容
4. **Importance**: 0.0-1.0，根据 JD 中的表述判断重要性
   - "精通"、"熟练掌握"、"核心职责" → 0.85-1.0
   - "熟悉"、"了解"、"有经验" → 0.7-0.85
   - "加分项"、"优先" → 0.6-0.7
5. **Expected Level**: 1-5 级别
   - L1: 基础了解
   - L2: 能使用
   - L3: 能深入应用和优化
   - L4: 能设计和架构
   - L5: 专家级/架构师级
6. **Evidence Expectation**: 2-3 个具体的验证点，描述面试中应该验证什么
7. **Inferred Level**: 根据整体 JD 判断岗位级别（intern/junior/mid/senior/staff）
8. **Inferred Round**: 根据 JD 内容判断适合的面试轮次

注意：
- 只提取明确提到的能力要求，不要臆测
- 如果某个技术或能力在列表中没有对应的 code，选择最接近的
- 同一个 competency_code 可能对应多个 requirement（如果 JD 中有多处提及不同方面）
- 不要遗漏重要的技能要求

请返回结构化的 JSON 格式结果。"""

    async def parse_jd(self, jd_text: str) -> JDParseResult:
        """Parse JD text and extract structured requirements.

        Args:
            jd_text: Raw JD text

        Returns:
            JDParseResult with parsed requirements

        Raises:
            ValueError: If JD text is empty or parsing fails
        """
        if not jd_text or not jd_text.strip():
            raise ValueError("JD text cannot be empty")

        prompt = self._build_prompt(jd_text)

        try:
            result = await self.llm.generate_structured(
                task_name="jd_parse",
                prompt=prompt,
                output_model=JDParseResult,
                temperature=0.3,  # Low temperature for more consistent extraction
            )

            # Validate that competency codes exist
            for req in result.requirements:
                if get_competency_by_code(req.competency_code) is None:
                    # Try to find closest match or raise error
                    raise ValueError(
                        f"Invalid competency code: {req.competency_code}. "
                        f"Must be one of: {', '.join(get_all_competency_codes())}"
                    )

            return result

        except Exception as e:
            raise ValueError(f"Failed to parse JD: {str(e)}")

    def validate_requirement(self, req: ParsedRequirement) -> list[str]:
        """Validate a parsed requirement and return list of issues.

        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []

        # Check competency code exists
        if get_competency_by_code(req.competency_code) is None:
            issues.append(f"Unknown competency code: {req.competency_code}")

        # Check importance range
        if not (0.0 <= req.importance <= 1.0):
            issues.append(f"Importance must be 0.0-1.0, got {req.importance}")

        # Check expected level range
        if not (1 <= req.expected_level <= 5):
            issues.append(f"Expected level must be 1-5, got {req.expected_level}")

        # Check evidence expectations
        if len(req.evidence_expectation) < 2:
            issues.append("Must have at least 2 evidence expectations")

        for evidence in req.evidence_expectation:
            if len(evidence) < 5:
                issues.append(f"Evidence expectation too short: {evidence}")

        return issues


# ============================================================
# Mock LLM for Testing
# ============================================================

class MockLLMGateway:
    """Mock LLM gateway for testing without real API calls."""

    async def generate_structured(
        self,
        task_name: str,
        prompt: str,
        output_model: type[BaseModel],
        **kwargs
    ) -> BaseModel:
        """Return mock parsed result."""
        # Simple mock: return a basic requirement structure
        if output_model == JDParseResult:
            return JDParseResult(
                requirements=[
                    ParsedRequirement(
                        competency_code="backend.cache",
                        title="Redis 缓存",
                        description="使用 Redis 实现缓存方案，处理高并发场景",
                        importance=0.85,
                        expected_level=3,
                        evidence_expectation=[
                            "能说明缓存模式（cache-aside, read-through）",
                            "能处理缓存一致性问题",
                            "能设计缓存 key 和过期策略",
                        ],
                    ),
                    ParsedRequirement(
                        competency_code="backend.database_modeling",
                        title="MySQL 优化",
                        description="MySQL 数据库设计和查询优化",
                        importance=0.9,
                        expected_level=3,
                        evidence_expectation=[
                            "能设计归一化 schema",
                            "能使用索引优化查询",
                            "能分析慢查询并优化",
                        ],
                    ),
                ],
                inferred_level="mid",
                inferred_round="technical",
            )

        raise ValueError(f"Unsupported output model: {output_model}")
