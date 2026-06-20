import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.templates import templates

logger = logging.getLogger(__name__)


def is_html_request(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept


def error_response(
    *,
    detail: Any,
    error_code: str,
    status_code: int,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "error_code": error_code},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse | HTMLResponse:
        if is_html_request(request):
            return templates.TemplateResponse(
                request=request,
                name="error.html",
                context={
                    "status_code": exc.status_code,
                    "detail": str(exc.detail),
                    "title": f"{exc.status_code} — UNSAID",
                },
                status_code=exc.status_code,
            )
        return error_response(
            detail=exc.detail,
            error_code="HTTP_ERROR",
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return error_response(
            detail=exc.errors(),
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse | HTMLResponse:
        logger.exception("Unhandled exception: %s", exc)
        if is_html_request(request):
            return templates.TemplateResponse(
                request=request,
                name="error.html",
                context={
                    "status_code": 500,
                    "detail": str(exc) if settings.debug else "Internal server error",
                    "title": "500 — UNSAID",
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        detail = str(exc) if settings.debug else "Internal server error"
        return error_response(
            detail=detail,
            error_code="INTERNAL_SERVER_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )