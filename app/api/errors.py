from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": _get_request_id(request),
            }
        },
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "request_id": _get_request_id(request),
            }
        },
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    field_errors = []
    for error in exc.errors():
        field_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "code": error.get("type", "validation_error"),
            "message": error.get("msg", "Validation failed"),
        })
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "field_errors": field_errors,
                "request_id": _get_request_id(request),
            }
        },
    )
