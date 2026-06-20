import hashlib
import hmac
import secrets
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

CSRF_COOKIE_NAME = "unsaid_csrf"
CSRF_FORM_FIELD = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_TOKEN_LENGTH = 32
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def generate_csrf_token() -> str:
    raw = secrets.token_hex(CSRF_TOKEN_LENGTH)
    signature = hmac.new(
        settings.session_secret_key.encode(),
        raw.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{raw}.{signature}"


def validate_csrf_token(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    raw, signature = token.rsplit(".", 1)
    expected = hmac.new(
        settings.session_secret_key.encode(),
        raw.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


class CSRFMiddleware(BaseHTTPMiddleware):
    def _ensure_csrf_cookie(self, request: Request, response: Response) -> None:
        existing = request.cookies.get(CSRF_COOKIE_NAME)
        if not existing or not validate_csrf_token(existing):
            response.set_cookie(
                CSRF_COOKIE_NAME,
                generate_csrf_token(),
                httponly=False,
                samesite="lax",
                secure=settings.session_cookie_secure,
                max_age=60 * 60 * 24,
            )

    def _get_cookie_token(self, request: Request) -> str:
        return request.cookies.get(CSRF_COOKIE_NAME) or ""

    def _get_header_token(self, request: Request) -> str:
        return request.headers.get(CSRF_HEADER_NAME, "")

    async def _parse_form_token(self, request: Request) -> str:
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            try:
                form = await request.form()
                return str(form.get(CSRF_FORM_FIELD, ""))
            except Exception:
                pass
        return ""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method in SAFE_METHODS:
            response = await call_next(request)
            self._ensure_csrf_cookie(request, response)
            return response

        form_token = await self._parse_form_token(request)
        header_token = self._get_header_token(request)
        cookie_token = self._get_cookie_token(request)

        form_matches = form_token and hmac.compare_digest(form_token, cookie_token)
        header_matches = header_token and hmac.compare_digest(header_token, cookie_token)
        if not cookie_token or not (form_matches or header_matches):
            return Response("CSRF token validation failed", status_code=403)

        response = await call_next(request)
        self._ensure_csrf_cookie(request, response)
        return response
