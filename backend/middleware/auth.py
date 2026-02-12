"""
API key authentication middleware.

When WAYFINDER_API_KEY is set, all requests (except /health) must include
a matching X-Api-Key header. When the env var is unset, auth is skipped
so local development works without configuration.
"""

import os
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("wayfinder.auth")

# Paths that never require authentication
EXEMPT_PATHS = {"/health", "/", "/docs", "/openapi.json", "/redoc"}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Validate X-Api-Key header against WAYFINDER_API_KEY env var."""

    async def dispatch(self, request: Request, call_next):
        expected_key = os.getenv("WAYFINDER_API_KEY")

        # No key configured → skip auth (local dev mode)
        if not expected_key:
            return await call_next(request)

        # Exempt certain paths (health checks, root, docs)
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Allow static file requests (frontend assets)
        if not request.url.path.startswith("/api") and not request.url.path.startswith("/mcp"):
            return await call_next(request)

        # Check the API key header
        provided_key = request.headers.get("X-Api-Key", "")
        if provided_key != expected_key:
            logger.warning(f"Rejected request to {request.url.path}: invalid or missing API key")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)
