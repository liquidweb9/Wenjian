"""Counterfactual question generator.

M2.4: Generates "what if" questions that change project constraints
to test transfer ability and adaptability.
"""

from typing import Any


class CounterfactualGenerator:
    """Generates counterfactual questions from confirmed project facts."""

    def generate_constraint_changes(
        self,
        project_context: dict[str, Any],
        verified_facts: list[str],
    ) -> list[dict[str, Any]]:
        """Generate realistic constraint changes for counterfactual questions.

        Args:
            project_context: Project details (title, role, summary, tech stack)
            verified_facts: List of verified facts from previous answers

        Returns:
            List of constraint change scenarios with:
            - change_type: scale, dependency, cost, timeline, team, requirement
            - description: Human-readable description of the change
            - original_constraint: The original constraint
            - new_constraint: The changed constraint
        """
        scenarios = []

        # Extract key facts from project context
        tech_stack = project_context.get("tech_stack", [])
        scale_info = self._extract_scale_info(verified_facts)

        # Scale changes (10x, 100x users/requests/data)
        if scale_info:
            scenarios.append({
                "change_type": "scale",
                "description": f"如果{scale_info['metric']}从{scale_info['current']}增加到{scale_info['increased']}倍",
                "original_constraint": scale_info["current"],
                "new_constraint": scale_info["increased"],
                "question_template": f"如果{scale_info['metric']}增加到{scale_info['increased']}倍，你的方案中哪些部分会成为瓶颈？你会如何调整架构？",
            })

        # Dependency failures (database down, cache unavailable, network partition)
        if tech_stack:
            for tech in tech_stack[:2]:  # Top 2 dependencies
                scenarios.append({
                    "change_type": "dependency",
                    "description": f"如果{tech}不可用",
                    "original_constraint": f"{tech}可用",
                    "new_constraint": f"{tech}故障或降级",
                    "question_template": f"如果{tech}出现故障或性能严重降级，你的系统会如何表现？有什么降级策略？",
                })

        # Cost constraints (need to reduce cost by 50%)
        scenarios.append({
            "change_type": "cost",
            "description": "需要将成本降低50%",
            "original_constraint": "当前成本结构",
            "new_constraint": "成本减半",
            "question_template": "如果需要将这个系统的运营成本降低50%，你会从哪些方面入手？哪些功能可能需要权衡？",
        })

        # Timeline changes (need to deliver in 1/3 time)
        scenarios.append({
            "change_type": "timeline",
            "description": "交付时间缩短到原计划的1/3",
            "original_constraint": project_context.get("timeline", "正常开发周期"),
            "new_constraint": "紧急上线要求",
            "question_template": "如果这个项目需要在极短时间内上线（原计划的1/3），你会如何调整范围和实现方案？",
        })

        # Team size changes (only 2 engineers instead of full team)
        scenarios.append({
            "change_type": "team",
            "description": "团队规模缩减到2人",
            "original_constraint": project_context.get("team_size", "完整团队"),
            "new_constraint": "小团队（2人）",
            "question_template": "如果这个项目只有2个工程师来开发维护（而不是完整团队），你会如何简化架构和技术选型？",
        })

        # Requirement changes (need to support new use case)
        scenarios.append({
            "change_type": "requirement",
            "description": "需要支持新的业务场景",
            "original_constraint": "当前需求范围",
            "new_constraint": "扩展需求（实时性/多租户/国际化等）",
            "question_template": "如果这个系统后来需要支持[实时查询/多租户隔离/国际化部署]，你当初的设计有哪些地方需要重构？如果重做会提前考虑什么？",
        })

        return scenarios

    def _extract_scale_info(self, verified_facts: list[str]) -> dict[str, Any] | None:
        """Extract scale information from verified facts.

        Args:
            verified_facts: List of verified fact strings

        Returns:
            Scale info dict or None if no scale mentioned
        """
        # Look for scale indicators in facts
        scale_keywords = {
            "QPS": {"current": "1000 QPS", "increased": "10万 QPS"},
            "用户": {"current": "10万用户", "increased": "1000万用户"},
            "数据": {"current": "GB级", "increased": "TB级"},
            "请求": {"current": "每秒千次", "increased": "每秒十万次"},
        }

        for fact in verified_facts:
            for keyword, scale_info in scale_keywords.items():
                if keyword in fact:
                    return {
                        "metric": keyword,
                        "current": scale_info["current"],
                        "increased": scale_info["increased"],
                    }

        # Default scale scenario if no specific scale mentioned
        return {
            "metric": "系统负载",
            "current": "当前水平",
            "increased": "10倍以上",
        }

    def build_counterfactual_question(
        self,
        scenario: dict[str, Any],
        project_name: str,
        depth: int,
    ) -> str:
        """Build a counterfactual question from a scenario.

        Args:
            scenario: Constraint change scenario
            project_name: Name of the project
            depth: Current depth level (affects question complexity)

        Returns:
            Formatted counterfactual question text
        """
        template = scenario.get("question_template", "")

        # Add depth-specific framing
        if depth >= 7:
            # Deep counterfactual: ask for complete redesign
            prefix = f"假设「{project_name}」项目需要在以下约束下重新设计：{scenario['description']}。"
            suffix = "请详细说明你会如何调整架构、技术选型、实现方案，以及这样调整的理由。"
        elif depth >= 6:
            # Mid-level counterfactual: ask for specific changes
            prefix = f"在「{project_name}」项目中，{scenario['description']}。"
            suffix = "你会调整哪些设计决策？为什么？"
        else:
            # Shallow counterfactual: ask for impact analysis
            prefix = f"在「{project_name}」项目中，{scenario['description']}。"
            suffix = "这会对你的方案产生什么影响？"

        if template:
            return f"{prefix}\n\n{template}\n\n{suffix}"
        else:
            return f"{prefix}\n\n{suffix}"
