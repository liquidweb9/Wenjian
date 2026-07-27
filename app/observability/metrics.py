"""Application metrics - placeholder for production monitoring."""

import time
from functools import wraps
from app.observability.logging import logger


def log_metric(task_name: str, **kwargs):
    logger.info("metric", task_name=task_name, **kwargs)


def timed(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.monotonic()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.monotonic() - start
            log_metric(func.__name__, latency_ms=round(elapsed * 1000), status="ok")
            return result
        except Exception as e:
            elapsed = time.monotonic() - start
            log_metric(func.__name__, latency_ms=round(elapsed * 1000), status="error", error=str(e))
            raise
    return wrapper
