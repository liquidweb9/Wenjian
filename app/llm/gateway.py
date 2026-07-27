"""Unified LLM Gateway - interface for all LLM calls."""

from typing import Protocol
from pydantic import BaseModel


class LLMGateway(Protocol):
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
        ...

    async def generate_text(
        self,
        *,
        task_name: str,
        system_prompt: str,
        user_prompt: str,
        model_tier: str = "balanced",
        temperature: float = 0,
    ) -> str:
        ...
