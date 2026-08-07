"""Agnes API (OpenAI-compatible) LLM implementation."""

import json
import time
from typing import Any, Callable

import httpx
from json_repair import repair_json
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import detect_injection_signal, sanitize_for_log, wrap_user_data
from app.llm.gateway import LLMGateway
from app.llm.retry import retry_llm_call
from app.observability.logging import logger

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
        system_prompt: str | None = None,
        user_payload: dict | None = None,
        output_model: type[BaseModel],
        model_tier: str = "balanced",
        temperature: float | None = None,
        reasoning_effort: str = "none",
        stream: bool = False,
        messages: list[dict] | None = None,
        repair: Callable[[dict], dict] | None = None,
    ) -> BaseModel:
        model = MODEL_TIER_MAP.get(model_tier, settings.llm_model_balanced)
        if temperature is None:
            temperature = self.default_temperature

        # Prompt injection detection
        if messages is not None:
            payload_str = json.dumps(messages, ensure_ascii=False)
            if detect_injection_signal(payload_str):
                logger.warning("injection_signal_detected", task=task_name)
            chat_messages = list(messages)
        else:
            payload_str = json.dumps(user_payload, ensure_ascii=False)
            if detect_injection_signal(payload_str) or detect_injection_signal(system_prompt or ""):
                logger.warning("injection_signal_detected", task=task_name)

            user_content = wrap_user_data(payload_str)

            chat_messages = [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": user_content},
            ]

        # Add JSON schema instruction
        schema = output_model.model_json_schema()
        chat_messages.append({
            "role": "system",
            "content": f"Respond ONLY with a valid JSON object matching this schema: {json.dumps(schema, ensure_ascii=False)}",
        })

        start_time = time.monotonic()
        raw, token_usage = await self._chat_completion(
            model=model,
            messages=chat_messages,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
            stream=stream,
        )
        latency_ms = round((time.monotonic() - start_time) * 1000)

        logger.info(
            "llm_call",
            task=task_name,
            model=model,
            tier=model_tier,
            input_tokens=token_usage.get("prompt_tokens"),
            output_tokens=token_usage.get("completion_tokens"),
            latency_ms=latency_ms,
            status="ok",
            stream=stream,
            input_preview=sanitize_for_log(json.dumps(user_payload if messages is None else messages, ensure_ascii=False), 800),
            output_preview=sanitize_for_log(raw, 800),
        )

        # Parse JSON from response
        parsed = self._parse_json(raw)
        if repair is not None:
            parsed = repair(parsed)
        return output_model.model_validate(parsed)

    @retry_llm_call(max_retries=3)
    async def generate_text(
        self,
        *,
        task_name: str,
        system_prompt: str,
        user_prompt: str,
        model_tier: str = "balanced",
        temperature: float | None = None,
        reasoning_effort: str = "none",
        stream: bool = False,
    ) -> str:
        model = MODEL_TIER_MAP.get(model_tier, settings.llm_model_balanced)
        if temperature is None:
            temperature = self.default_temperature

        # Prompt injection detection
        if detect_injection_signal(user_prompt) or detect_injection_signal(system_prompt):
            logger.warning("injection_signal_detected", task=task_name)

        wrapped = wrap_user_data(user_prompt)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": wrapped},
        ]

        start_time = time.monotonic()
        content, token_usage = await self._chat_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
            stream=stream,
        )
        latency_ms = round((time.monotonic() - start_time) * 1000)

        logger.info(
            "llm_call",
            task=task_name,
            model=model,
            tier=model_tier,
            input_tokens=token_usage.get("prompt_tokens"),
            output_tokens=token_usage.get("completion_tokens"),
            latency_ms=latency_ms,
            status="ok",
            stream=stream,
            input_preview=sanitize_for_log(user_prompt, 800),
            output_preview=sanitize_for_log(content, 800),
        )
        return content

    async def _chat_completion(
        self,
        *,
        model: str,
        messages: list[dict],
        temperature: float,
        reasoning_effort: str,
        stream: bool,
    ) -> tuple[str, dict]:
        """POST /chat/completions and return (content, token_usage).

        In streaming mode the SSE payload is aggregated into the final content
        string; this keeps long-running generations alive past provider-side
        response timeouts that only trigger when no bytes have been sent yet.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
            "reasoning_effort": reasoning_effort,
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
            if stream:
                content_parts: list[str] = []
                usage: dict = {}
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json={**payload, "stream": True},
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[len("data:"):].strip()
                        if data_str == "[DONE]":
                            break
                        chunk = json.loads(data_str)
                        if chunk.get("usage"):
                            usage = chunk["usage"]
                        choices = chunk.get("choices") or []
                        if choices:
                            delta = choices[0].get("delta") or {}
                            if delta.get("content"):
                                content_parts.append(delta["content"])
                return "".join(content_parts), usage
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"], data.get("usage", {})

    def _parse_json(self, raw: str) -> dict[str, Any]:
        """Extract JSON from LLM response, handling common malformed output.

        LLM providers frequently emit trailing prose, markdown fences, or
        unescaped control characters (raw newlines/tabs) inside string values.
        Repair those cases before falling back to a strict parse.
        """
        # Remove markdown code block fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        # Extract the JSON object span, ignoring leading/trailing prose
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            raw = raw[start : end + 1]

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            repaired = _escape_string_control_chars(raw)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError as e:
                # Last-resort structural repair: LLMs occasionally drop the
                # opening '{' of array-of-object elements (e.g. a "dimensions"
                # list where later objects are emitted as bare "key": value
                # runs). json-repair rebalances braces so the text parses.
                try:
                    structure_repaired = repair_json(repaired)
                    return json.loads(structure_repaired)
                except (json.JSONDecodeError, TypeError, ValueError) as e2:
                    logger.warning(
                        "json_parse_failed",
                        error=str(e)[:120],
                        repair_error=str(e2)[:120],
                        raw_preview=sanitize_for_log(raw, 400),
                    )
                    raise


_JSON_STRING_ESCAPES = {"\n": "n", "\r": "r", "\t": "t", "\b": "b", "\f": "f"}


def _escape_string_control_chars(text: str) -> str:
    """Escape raw control characters that appear inside JSON string literals.

    LLMs often emit literal newlines/tabs within string values, which is invalid
    JSON. Walk the text tracking string boundaries so structural whitespace
    outside strings is left untouched.
    """
    out: list[str] = []
    in_string = False
    escaped = False
    for ch in text:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\":
            out.append(ch)
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ch in _JSON_STRING_ESCAPES:
            out.append("\\" + _JSON_STRING_ESCAPES[ch])
            continue
        out.append(ch)
    return "".join(out)
