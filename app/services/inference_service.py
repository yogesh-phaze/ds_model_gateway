import asyncio
import logging
import time
from typing import Awaitable, Callable, TypeVar

import httpx

from app.clients.clip_embed_client import ClipEmbedClient
from app.clients.octen_client import OctenEmbedClient
from app.config import MODEL_REGISTRY, ModelConfig, settings
from app.metrics import (
    MODEL_ERRORS_TOTAL,
    MODEL_INFERENCE_DURATION_SECONDS,
    MODEL_INFLIGHT_REQUESTS,
)
from app.schemas.embedding import TextEmbeddingRequest

logger = logging.getLogger("gateway.inference")

T = TypeVar("T")


class InferenceService:
    def __init__(self):
        self.octen_client = OctenEmbedClient()
        self.clip_client = ClipEmbedClient()

        # Global cap across all models, on top of each model's own limit.
        self.global_semaphore = asyncio.Semaphore(
            settings.GATEWAY_MAX_CONCURRENCY
        )

        self.semaphores = {
            model_name: asyncio.Semaphore(
                config.max_concurrency
            )
            for model_name, config in MODEL_REGISTRY.items()
        }

    async def _call(
        self,
        model_name: str,
        request_id: str,
        call: Callable[[ModelConfig], Awaitable[T]],
    ) -> T:

        model = MODEL_REGISTRY[model_name]
        semaphore = self.semaphores[model_name]

        async with self.global_semaphore, semaphore:

            MODEL_INFLIGHT_REQUESTS.labels(model_name).inc()
            start = time.perf_counter()

            try:
                return await call(model)

            except httpx.TimeoutException:
                MODEL_ERRORS_TOTAL.labels(model_name, "timeout").inc()
                raise

            except httpx.HTTPStatusError:
                MODEL_ERRORS_TOTAL.labels(model_name, "http_status").inc()
                raise

            except httpx.RequestError:
                MODEL_ERRORS_TOTAL.labels(model_name, "unreachable").inc()
                raise

            except Exception:
                MODEL_ERRORS_TOTAL.labels(model_name, "unknown").inc()
                raise

            finally:
                duration = time.perf_counter() - start

                MODEL_INFLIGHT_REQUESTS.labels(model_name).dec()
                MODEL_INFERENCE_DURATION_SECONDS.labels(model_name).observe(
                    duration
                )

                logger.info(
                    "model_inference_completed",
                    extra={
                        "request_id": request_id,
                        "model": model_name,
                        "duration_ms": round(duration * 1000, 2),
                    },
                )

    async def embed_text(
        self,
        model_name: str,
        request: TextEmbeddingRequest,
        request_id: str,
    ) -> list[list[float]]:

        return await self._call(
            model_name,
            request_id,
            lambda model: self.octen_client.embed(model, request),
        )

    async def embed_image(
        self,
        model_name: str,
        filename: str,
        content_type: str,
        content: bytes,
        normalize: bool,
        request_id: str,
    ) -> list[float]:

        return await self._call(
            model_name,
            request_id,
            lambda model: self.clip_client.embed_image(
                model, filename, content_type, content, normalize
            ),
        )


inference_service = InferenceService()
