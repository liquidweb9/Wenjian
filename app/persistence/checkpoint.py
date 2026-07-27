"""LangGraph checkpointer using Postgres (or MemorySaver for dev)."""

from app.core.config import settings
from app.observability.logging import logger


def create_checkpointer():
    """Create a checkpointer for LangGraph.

    Uses PostgresSaver in production, MemorySaver in development/test.
    """
    if settings.app_env == "production":
        from langgraph.checkpoint.postgres import PostgresSaver
        connection_string = settings.database_url_sync
        logger.info("using_postgres_checkpointer")
        return PostgresSaver(connection_string)
    else:
        from langgraph.checkpoint.memory import MemorySaver
        logger.info("using_memory_checkpointer")
        return MemorySaver()
