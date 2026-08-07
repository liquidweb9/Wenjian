"""LLM call retry logic."""

import asyncio
import functools
import ssl

import httpx
from pydantic import ValidationError

from app.observability.logging import logger


def retry_llm_call(max_retries: int = 3):
    """Decorator for retrying LLM calls on transient errors."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    status = e.response.status_code
                    if status in (429, 502, 503, 504):
                        last_error = e
                        wait = 2 ** attempt
                        logger.warning("llm_retry", attempt=attempt + 1, status=status, wait=wait)
                        await asyncio.sleep(wait)
                        continue
                    raise
                except httpx.TimeoutException as e:
                    last_error = e
                    wait = 2 ** attempt
                    logger.warning("llm_retry_timeout", attempt=attempt + 1, wait=wait)
                    await asyncio.sleep(wait)
                    continue
                except (httpx.TransportError, ssl.SSLError) as e:
                    # Transient connection/TLS failures, e.g. "[SSL] record layer
                    # failure", which httpx does not map to a status code.
                    last_error = e
                    wait = 2 ** attempt
                    logger.warning("llm_retry_transport", attempt=attempt + 1, error=str(e)[:120], wait=wait)
                    await asyncio.sleep(wait)
                    continue
                except ValidationError as e:
                    last_error = e
                    logger.warning("llm_retry_schema", attempt=attempt + 1, error=str(e))
                    continue
                except ValueError as e:
                    # Catches json.JSONDecodeError from _parse_json
                    last_error = e
                    logger.warning("llm_retry_parse", attempt=attempt + 1, error=str(e)[:100])
                    await asyncio.sleep(2 ** attempt)
                    continue
            raise last_error or RuntimeError("LLM call failed after retries")
        return wrapper
    return decorator
