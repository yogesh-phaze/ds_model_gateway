from fastapi import APIRouter
import httpx

from app.config import MODEL_REGISTRY


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/live")
async def liveness():

    return {
        "status": "ok",
    }


@router.get("/ready")
async def readiness():

    models = {}

    async with httpx.AsyncClient(timeout=5.0) as client:

        for name, config in MODEL_REGISTRY.items():

            try:

                response = await client.get(
                    f"{config.base_url}/health"
                )

                models[name] = (
                    "ready"
                    if response.is_success
                    else "not_ready"
                )

            except Exception:

                models[name] = "unavailable"

    all_ready = all(
        status == "ready"
        for status in models.values()
    )

    return {
        "status": "ready" if all_ready else "not_ready",
        "models": models,
    }