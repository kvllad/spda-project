from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger
from app.core.metrics import REQUEST_COUNT, REQUEST_DURATION


class ObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._logger = get_logger("app.http")

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        started_at = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            duration = perf_counter() - started_at
            route_path = self._resolve_path(request)
            REQUEST_COUNT.labels(
                method=request.method,
                path=route_path,
                status_code=str(status_code),
            ).inc()
            REQUEST_DURATION.labels(method=request.method, path=route_path).observe(duration)
            self._logger.exception(
                "http_request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "route_path": route_path,
                    "status_code": status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "client": request.client.host if request.client else None,
                },
            )
            raise

        duration = perf_counter() - started_at
        route_path = self._resolve_path(request)
        REQUEST_COUNT.labels(
            method=request.method,
            path=route_path,
            status_code=str(status_code),
        ).inc()
        REQUEST_DURATION.labels(method=request.method, path=route_path).observe(duration)
        self._logger.info(
            "http_request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "route_path": route_path,
                "status_code": status_code,
                "duration_ms": round(duration * 1000, 2),
                "client": request.client.host if request.client else None,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response

    @staticmethod
    def _resolve_path(request: Request) -> str:
        route = request.scope.get("route")
        if route and getattr(route, "path", None):
            return route.path
        return request.url.path
