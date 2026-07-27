"""Helper to build structured prompts with JSON schema instructions."""

from pydantic import BaseModel
import json


def build_structured_prompt(
    instruction: str,
    output_model: type[BaseModel],
    examples: list[dict] | None = None,
) -> str:
    """Build a system prompt that requests structured JSON output."""
    schema = output_model.model_json_schema()
    prompt = f"{instruction}\n\nYou must respond with a valid JSON object matching this schema:\n{json.dumps(schema, indent=2, ensure_ascii=False)}"

    if examples:
        prompt += "\n\nExamples:\n"
        for ex in examples:
            prompt += json.dumps(ex, ensure_ascii=False) + "\n"

    prompt += "\n\nRespond ONLY with the JSON object, no other text."
    return prompt
