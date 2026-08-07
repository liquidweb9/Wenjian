"""Unified LLM Gateway - interface for all LLM calls."""

from typing import Callable, Protocol

from pydantic import BaseModel


class LLMGateway(Protocol):
    async def generate_structured(
        self,
        *,
        task_name: str,
        system_prompt: str | None = None,
        user_payload: dict | None = None,
        output_model: type[BaseModel],
        model_tier: str = "balanced",
        temperature: float | None = None,
        messages: list[dict] | None = None,
        repair: Callable[[dict], dict] | None = None,
    ) -> BaseModel:
        ...

    async def generate_text(
        self,
        *,
        task_name: str,
        system_prompt: str,
        user_prompt: str,
        model_tier: str = "balanced",
        temperature: float | None = None,
    ) -> str:
        ...
