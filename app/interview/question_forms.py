"""Question form types and selectors for multi-form ability verification.

M2.4: Ensures high-importance competencies are verified through multiple
question types to reduce coaching/memorization bias.
"""

from enum import Enum
from typing import Any


class QuestionForm(str, Enum):
    """Question form types for deep verification."""

    # Core understanding
    CONCEPT = "concept"  # Theoretical principles, definitions, mental models
    DESIGN_RATIONALE = "design_rationale"  # Why this design? What alternatives?

    # Implementation specifics
    PROJECT_DETAIL = "project_detail"  # Execution flow, code structure, interfaces
    DEBUGGING = "debugging"  # Problem diagnosis, troubleshooting, edge cases

    # Production awareness
    PRODUCTION_SCENARIO = "production_scenario"  # Failures, monitoring, operations
    TRADE_OFF = "trade_off"  # Performance vs. complexity, cost vs. reliability

    # Transfer and evolution
    COUNTERFACTUAL = "counterfactual"  # What if constraints changed?
    EVOLUTION = "evolution"  # How would you scale/improve this?


# Form characteristics for selection
FORM_CHARACTERISTICS = {
    QuestionForm.CONCEPT: {
        "depth_range": (1, 4),  # Suitable for depths 1-4
        "requires_project_context": False,
        "tests_ability": "theoretical_understanding",
        "description": "测试理论理解和概念清晰度",
    },
    QuestionForm.DESIGN_RATIONALE: {
        "depth_range": (4, 6),
        "requires_project_context": True,
        "tests_ability": "architectural_thinking",
        "description": "测试架构思维和决策能力",
    },
    QuestionForm.PROJECT_DETAIL: {
        "depth_range": (2, 5),
        "requires_project_context": True,
        "tests_ability": "implementation_depth",
        "description": "测试实现深度和细节掌握",
    },
    QuestionForm.DEBUGGING: {
        "depth_range": (3, 5),
        "requires_project_context": True,
        "tests_ability": "problem_solving",
        "description": "测试问题诊断和解决能力",
    },
    QuestionForm.PRODUCTION_SCENARIO: {
        "depth_range": (5, 7),
        "requires_project_context": True,
        "tests_ability": "production_awareness",
        "description": "测试生产环境意识",
    },
    QuestionForm.TRADE_OFF: {
        "depth_range": (4, 6),
        "requires_project_context": True,
        "tests_ability": "tradeoff_analysis",
        "description": "测试权衡分析能力",
    },
    QuestionForm.COUNTERFACTUAL: {
        "depth_range": (6, 7),
        "requires_project_context": True,
        "tests_ability": "transfer_ability",
        "description": "测试迁移能力和适应性",
    },
    QuestionForm.EVOLUTION: {
        "depth_range": (6, 7),
        "requires_project_context": True,
        "tests_ability": "evolution_thinking",
        "description": "测试演进思维和扩展能力",
    },
}


class QuestionFormSelector:
    """Selects appropriate question forms avoiding repetition."""

    def __init__(self):
        self._form_history: dict[str, list[QuestionForm]] = {}  # competency_code -> forms used

    def select_form(
        self,
        competency_code: str,
        current_depth: int,
        project_context_available: bool,
        form_history: list[str] | None = None,
    ) -> QuestionForm:
        """Select a question form for the given competency.

        Args:
            competency_code: Competency being verified
            current_depth: Current depth level (1-7)
            project_context_available: Whether project details are available
            form_history: Previously used forms for this competency (from state)

        Returns:
            Selected QuestionForm
        """
        # Convert form_history strings to enums
        used_forms = set()
        if form_history:
            for form_str in form_history:
                try:
                    used_forms.add(QuestionForm(form_str))
                except ValueError:
                    pass

        # Find suitable forms for current depth
        suitable_forms = []
        for form, chars in FORM_CHARACTERISTICS.items():
            min_depth, max_depth = chars["depth_range"]

            # Check depth range
            if not (min_depth <= current_depth <= max_depth):
                continue

            # Check project context requirement
            if chars["requires_project_context"] and not project_context_available:
                continue

            # Check if already used
            if form in used_forms:
                continue

            suitable_forms.append(form)

        # If all forms used, allow repetition but prefer less-used ones
        if not suitable_forms:
            suitable_forms = [
                form for form, chars in FORM_CHARACTERISTICS.items()
                if (chars["depth_range"][0] <= current_depth <= chars["depth_range"][1])
                and (not chars["requires_project_context"] or project_context_available)
            ]

        # Prioritize by depth-form matching and diversity
        if not suitable_forms:
            # Fallback to PROJECT_DETAIL if nothing else fits
            return QuestionForm.PROJECT_DETAIL

        # For depths 1-2: prefer CONCEPT or PROJECT_DETAIL
        if current_depth <= 2:
            if QuestionForm.CONCEPT in suitable_forms:
                return QuestionForm.CONCEPT
            if QuestionForm.PROJECT_DETAIL in suitable_forms:
                return QuestionForm.PROJECT_DETAIL

        # For depths 3-4: prefer PROJECT_DETAIL, DESIGN_RATIONALE, DEBUGGING
        elif current_depth <= 4:
            for form in [QuestionForm.PROJECT_DETAIL, QuestionForm.DESIGN_RATIONALE, QuestionForm.DEBUGGING]:
                if form in suitable_forms:
                    return form

        # For depths 5-6: prefer TRADE_OFF, PRODUCTION_SCENARIO, DESIGN_RATIONALE
        elif current_depth <= 6:
            for form in [QuestionForm.TRADE_OFF, QuestionForm.PRODUCTION_SCENARIO, QuestionForm.DESIGN_RATIONALE]:
                if form in suitable_forms:
                    return form

        # For depth 7: prefer COUNTERFACTUAL, EVOLUTION
        else:
            for form in [QuestionForm.COUNTERFACTUAL, QuestionForm.EVOLUTION]:
                if form in suitable_forms:
                    return form

        # Default to first suitable form
        return suitable_forms[0]

    def get_form_coverage(self, form_history: list[str]) -> dict[str, int]:
        """Calculate coverage statistics for forms.

        Args:
            form_history: List of form strings used

        Returns:
            Dict mapping form name to usage count
        """
        coverage = {form.value: 0 for form in QuestionForm}
        for form_str in form_history:
            if form_str in coverage:
                coverage[form_str] += 1
        return coverage

    def get_untested_abilities(self, form_history: list[str]) -> list[str]:
        """Get list of abilities not yet tested.

        Args:
            form_history: List of form strings used

        Returns:
            List of ability names not yet tested
        """
        used_forms = set(form_history)
        tested_abilities = set()

        for form_str in used_forms:
            try:
                form = QuestionForm(form_str)
                ability = FORM_CHARACTERISTICS[form]["tests_ability"]
                tested_abilities.add(ability)
            except (ValueError, KeyError):
                pass

        all_abilities = {chars["tests_ability"] for chars in FORM_CHARACTERISTICS.values()}
        untested = list(all_abilities - tested_abilities)
        return untested


def get_form_prompt_guidance(form: QuestionForm, depth: int) -> str:
    """Get prompt guidance for generating a specific question form.

    Args:
        form: Question form type
        depth: Current depth level

    Returns:
        Guidance text to append to question generation prompt
    """
    guidance_map = {
        QuestionForm.CONCEPT: (
            "生成一个概念理解类问题：\n"
            "- 测试候选人对核心概念、原理、定义的理解\n"
            "- 可以问「这个技术的工作原理是什么」「为什么需要这个概念」\n"
            "- 不要问代码细节，聚焦理论模型和心智模型"
        ),
        QuestionForm.DESIGN_RATIONALE: (
            "生成一个设计决策类问题：\n"
            "- 测试候选人的架构思维和决策能力\n"
            "- 问「为什么选择这个方案」「考虑了哪些替代方案」\n"
            "- 聚焦设计权衡和决策依据，而非实现细节"
        ),
        QuestionForm.PROJECT_DETAIL: (
            "生成一个实现细节类问题：\n"
            "- 测试候选人对代码结构、接口、数据流的掌握\n"
            "- 问「具体是如何实现的」「数据如何流转」「接口如何设计」\n"
            "- 聚焦执行流程和技术细节"
        ),
        QuestionForm.DEBUGGING: (
            "生成一个问题诊断类问题：\n"
            "- 测试候选人的故障排查和问题解决能力\n"
            "- 描述一个潜在故障场景，问「如何定位问题」「如何修复」\n"
            "- 聚焦诊断思路和排查方法"
        ),
        QuestionForm.PRODUCTION_SCENARIO: (
            "生成一个生产环境类问题：\n"
            "- 测试候选人的生产意识\n"
            "- 问「如何监控」「如何处理故障」「如何保证可用性」\n"
            "- 聚焦运维、容错、性能、安全等生产环境考虑"
        ),
        QuestionForm.TRADE_OFF: (
            "生成一个权衡分析类问题：\n"
            "- 测试候选人的方案权衡能力\n"
            "- 问「这个设计有什么代价」「性能和复杂度如何平衡」\n"
            "- 聚焦方案优缺点和权衡理由"
        ),
        QuestionForm.COUNTERFACTUAL: (
            "生成一个反事实类问题：\n"
            "- 测试候选人的迁移能力和适应性\n"
            "- 基于项目事实，改变约束条件，问「如果XXX改变，你会如何调整方案」\n"
            "- 聚焦约束变化后的方案适应"
        ),
        QuestionForm.EVOLUTION: (
            "生成一个演进类问题：\n"
            "- 测试候选人的扩展思维\n"
            "- 问「如果规模扩大10倍怎么办」「如果重做会怎么改进」\n"
            "- 聚焦系统演进和扩展能力"
        ),
    }

    return guidance_map.get(form, "")
