import logging

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.config import settings
from app.core.errors import register_exception_handlers
from app.logging_config import setup_logging
from app.middleware.metrics import MetricsMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.api.inference import router as inference_router
from app.api.health import router as health_router


setup_logging(settings.LOG_LEVEL)

logger = logging.getLogger("gateway.startup")


app = FastAPI(
    title="AI Inference Gateway",
    version="1.0.0",
)


# Added last so it is outermost: it must see every request first
# (to assign request_id) and every response last (to log status/duration).
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestContextMiddleware)

register_exception_handlers(app)


app.include_router(
    inference_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    health_router,
    prefix=settings.API_PREFIX,
)


@app.get("/metrics")
async def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/")
async def root():

    return {
        "service": settings.APP_NAME,
        "status": "running",
    }


@app.on_event("startup")
async def warn_on_default_api_key():
    if settings.API_KEYS == frozenset({"changeme-dev-key"}):
        logger.warning(
            "using_default_api_key: API_KEYS not set — using insecure "
            "default. Set API_KEYS before deploying."
        )
