import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("gateway.errors")


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _safe_validation_errors(exc: RequestValidationError) -> list[dict]:
    # exc.errors()[i]["ctx"] can hold the raw exception instance that
    # triggered a custom validator (e.g. a field_validator's ValueError),
    # which plain json.dumps can't serialize. Drop it; msg already has
    # the human-readable text.
    errors = []

    for error in exc.errors():
        error = dict(error)
        error.pop("ctx", None)
        errors.append(error)

    return jsonable_encoder(errors)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "request_id": _request_id(request),
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": _safe_validation_errors(exc),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ):
        detail = exc.detail

        if isinstance(detail, dict):
            body = {"request_id": _request_id(request), **detail}
        else:
            body = {
                "request_id": _request_id(request),
                "error": "HTTP_ERROR",
                "message": str(detail),
            }

        return JSONResponse(
            status_code=exc.status_code,
            content=body,
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "unhandled_exception",
            extra={"request_id": _request_id(request)},
        )

        return JSONResponse(
            status_code=500,
            content={
                "request_id": _request_id(request),
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
        )
