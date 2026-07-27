"""Token budget management - control context sent to LLM per node."""

import json


def truncate_for_llm(text: str, max_chars: int = 4000) -> str:
    """Truncate text to a maximum number of characters."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n... [truncated, original {len(text)} chars]"


def build_question_context(
    claim_text: str,
    source_text: str,
    verification_point: str,
    recent_qa: list[dict] | None = None,
    evidence_summary: str | None = None,
) -> dict:
    """Build the context dict for question generation, respecting token budgets."""
    context = {
        "claim": truncate_for_llm(claim_text, 1000),
        "source": truncate_for_llm(source_text, 1500),
        "verification_point": truncate_for_llm(verification_point, 500),
    }

    if recent_qa:
        context["recent_qa"] = recent_qa[-3:]  # Only last 3 Q&A pairs

    if evidence_summary:
        context["evidence_summary"] = truncate_for_llm(evidence_summary, 1000)

    return context
