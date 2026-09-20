from dataclasses import dataclass
import os


def _parse_keys(raw: str) -> frozenset[str]:
    return frozenset(
        key.strip() for key in raw.split(",") if key.strip()
    )


@dataclass(frozen=True)
class ModelConfig:
    name: str
    base_url: str
    timeout_seconds: float
    max_concurrency: int


class Settings:
    APP_NAME = os.getenv("APP_NAME", "ai-inference-gateway")
    API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Comma-separated list of accepted API keys, e.g. "key-one,key-two".
    API_KEYS = _parse_keys(
        os.getenv("API_KEYS", "changeme-dev-key")
    )

    RATE_LIMIT_REQUESTS = int(
        os.getenv("RATE_LIMIT_REQUESTS", "60")
    )

    RATE_LIMIT_WINDOW_SECONDS = float(
        os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    )

    # Hard cap on requests in flight across all models combined,
    # on top of each model's own concurrency limit below.
    GATEWAY_MAX_CONCURRENCY = int(
        os.getenv("GATEWAY_MAX_CONCURRENCY", "4")
    )

    # octen-embed-service container (llama-server, text embeddings),
    # reached by container name on the shared Docker network.
    OCTEN_EMBED_URL = os.getenv(
        "OCTEN_EMBED_URL",
        "http://octen-embed-service:8080",
    )

    # image_embedding_model-clip-embed-1 container (CLIP image/text embeddings).
    CLIP_EMBED_URL = os.getenv(
        "CLIP_EMBED_URL",
        "http://image_embedding_model-clip-embed-1:8001",
    )

    # Bearer token octen-embed-service was started with (--api-key).
    OCTEN_EMBED_API_KEY = os.getenv("OCTEN_EMBED_API_KEY", "")

    OCTEN_EMBED_TIMEOUT = float(
        os.getenv("OCTEN_EMBED_TIMEOUT", "30")
    )

    CLIP_EMBED_TIMEOUT = float(
        os.getenv("CLIP_EMBED_TIMEOUT", "30")
    )

    OCTEN_EMBED_MAX_CONCURRENCY = int(
        os.getenv("OCTEN_EMBED_MAX_CONCURRENCY", "1")
    )

    CLIP_EMBED_MAX_CONCURRENCY = int(
        os.getenv("CLIP_EMBED_MAX_CONCURRENCY", "1")
    )


settings = Settings()


MODEL_REGISTRY = {
    "octen-embed": ModelConfig(
        name="octen-embed",
        base_url=settings.OCTEN_EMBED_URL,
        timeout_seconds=settings.OCTEN_EMBED_TIMEOUT,
        max_concurrency=settings.OCTEN_EMBED_MAX_CONCURRENCY,
    ),
    "clip-embed": ModelConfig(
        name="clip-embed",
        base_url=settings.CLIP_EMBED_URL,
        timeout_seconds=settings.CLIP_EMBED_TIMEOUT,
        max_concurrency=settings.CLIP_EMBED_MAX_CONCURRENCY,
    ),
}
