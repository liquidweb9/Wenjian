import logging
from pathlib import Path

import structlog
from app.core.config import settings

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

renderer = (
    structlog.dev.ConsoleRenderer()
    if settings.app_debug
    else structlog.processors.JSONRenderer()
)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        renderer,
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(message)s"))
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(message)s"))

root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

for uvicorn_logger in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    logging.getLogger(uvicorn_logger).propagate = False

logger = structlog.get_logger()
