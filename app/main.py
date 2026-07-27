from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    app_error_handler,
    http_error_handler,
    validation_error_handler,
)
from app.api.middleware import RequestIDMiddleware
from app.api.v1 import health, resumes, interviews, reports, dashboard, analytics, auth
from app.core.config import settings
from app.core.exceptions import AppError
from app.observability.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_start", env=settings.app_env, model=settings.llm_model_balanced)
    yield
    logger.info("app_shutdown")


app = FastAPI(
    title="Resume Deep Interviewer",
    version="0.1.0",
    lifespan=lifespan,
)

# Request ID must be first so downstream handlers can read request.state.request_id
app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(StarletteHTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

# Routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(resumes.router, prefix="/api/v1")
app.include_router(interviews.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
