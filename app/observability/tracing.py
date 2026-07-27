"""Tracing placeholder for future OpenTelemetry integration."""

from contextlib import asynccontextmanager
from app.observability.logging import logger


@asynccontextmanager
async def trace_span(name: str, **attrs):
    logger.debug("span_start", name=name, **attrs)
    try:
        yield
    finally:
        logger.debug("span_end", name=name)
