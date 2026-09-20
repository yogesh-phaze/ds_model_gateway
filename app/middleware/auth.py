import hmac

from fastapi import Header, HTTPException

from app.config import settings
from app.metrics import AUTH_FAILURES_TOTAL


def _matches_any_key(candidate: str) -> bool:
    return any(
        hmac.compare_digest(candidate, key)
        for key in settings.API_KEYS
    )


async def require_api_key(
    x_api_key: str | None = Header(default=None),
) -> str:
    if x_api_key is None or not _matches_any_key(x_api_key):
        AUTH_FAILURES_TOTAL.inc()

        raise HTTPException(
            status_code=401,
            detail={
                "error": "UNAUTHORIZED",
                "message": "Missing or invalid API key",
            },
        )

    return x_api_key
