"""Agnes API (OpenAI-compatible) LLM implementation."""

import json
import time
from typing import Any
from pydantic import BaseModel
import httpx

from app.core.config import settings
from app.llm.gateway import LLMGateway
from app.llm.retry import retry_llm_call
from app.observability.logging import logger
from app.core.security import detect_injection_signal, wrap_user_data

MODEL_TIER_MAP = {
    "fast": settings.llm_model_fast,
    "balanced": settings.llm_model_balanced,
    "judge": settings.llm_model_judge,
}


class AgnesGateway(LLMGateway):
    def __init__(self):
        self.base_url = settings.llm_base_url
        self.api_key = settings.llm_api_key
        self.max_tokens = settings.llm_max_tokens
        self.default_temperature = settings.llm_temperature

    @retry_llm_call(max_retries=3)
    async def generate_structured(
        self,
        *,
        task_name: str,
        system_prompt: str,
        user_payload: dict,
        output_model: type[BaseModel],
        model_tier: str = "balanced",
        temperature: float = 0,
    ) -> BaseModel:
        model = MODEL_TIER_MAP.get(model_tier, settings.llm_model_balanced)

        # Prompt injection detection
        payload_str = json.dumps(user_payload, ensure_ascii=False)
        if detect_injection_signal(payload_str) or detect_injection_signal(system_prompt):
            logger.warning("injection_signal_detected", task=task_name)

        user_content = wrap_user_data(payload_str)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        # Add JSON schema instruction
        schema = output_model.model_json_schema()
        messages.append({
            "role": "system",
            "content": f"Respond ONLY with a valid JSON object matching this schema: {json.dumps(schema, ensure_ascii=False)}",
        })

        start_time = time.monotonic()
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": self.max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        latency_ms = round((time.monotonic() - start_time) * 1000)
        raw = data["choices"][0]["message"]["content"]
        token_usage = data.get("usage", {})

        logger.info(
            "llm_call",
            task=task_name,
            model=model,
            tier=model_tier,
            input_tokens=token_usage.get("prompt_tokens"),
            output_tokens=token_usage.get("completion_tokens"),
            latency_ms=latency_ms,
            status="ok",
        )

        # Parse JSON from response
        parsed = self._parse_json(raw)
        return output_model.model_validate(parsed)

    @retry_llm_call(max_retries=3)
    async def generate_text(
        self,
        *,
        task_name: str,
        system_prompt: str,
        user_prompt: str,
        model_tier: str = "balanced",
        temperature: float = 0,
    ) -> str:
        model = MODEL_TIER_MAP.get(model_tier, settings.llm_model_balanced)

        # Prompt injection detection
        if detect_injection_signal(user_prompt) or detect_injection_signal(system_prompt):
            logger.warning("injection_signal_detected", task=task_name)

        wrapped = wrap_user_data(user_prompt)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": wrapped},
        ]

        start_time = time.monotonic()
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": self.max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        latency_ms = round((time.monotonic() - start_time) * 1000)
        content = data["choices"][0]["message"]["content"]
        token_usage = data.get("usage", {})

        logger.info(
            "llm_call",
            task=task_name,
            model=model,
            tier=model_tier,
            input_tokens=token_usage.get("prompt_tokens"),
            output_tokens=token_usage.get("completion_tokens"),
            latency_ms=latency_ms,
            status="ok",
        )
        return content

    def _parse_json(self, raw: str) -> dict[str, Any]:
        """Extract JSON from LLM response, handling markdown fences."""
        # Remove markdown code block fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        return json.loads(raw.strip())
