import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.metrics import HTTP_REQUEST_DURATION_SECONDS, HTTP_REQUESTS_TOTAL


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        duration = time.perf_counter() - start

        route = request.scope.get("route")
        path = route.path if route is not None else request.url.path

        HTTP_REQUESTS_TOTAL.labels(
            request.method, path, response.status_code
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            request.method, path
        ).observe(duration)

        return response
