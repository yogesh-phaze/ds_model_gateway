from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
import httpx

from app.middleware.auth import require_api_key
from app.middleware.rate_limit import enforce_rate_limit
from app.schemas.embedding import EmbeddingResponse, TextEmbeddingRequest
from app.services.inference_service import inference_service


router = APIRouter(
    prefix="/inference",
    tags=["Inference"],
    dependencies=[
        Depends(require_api_key),
        Depends(enforce_rate_limit),
    ],
)

_ALLOWED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/bmp",
    "image/gif",
}

_MAX_IMAGE_BYTES = 10 * 1024 * 1024


@router.post(
    "/octen-embed/embed",
    response_model=EmbeddingResponse,
)
async def embed_text(
    request: TextEmbeddingRequest,
    http_request: Request,
):

    request_id = http_request.state.request_id

    try:

        embeddings = await inference_service.embed_text(
            model_name="octen-embed",
            request=request,
            request_id=request_id,
        )

    except httpx.TimeoutException as exc:

        raise HTTPException(
            status_code=504,
            detail={
                "error": "MODEL_TIMEOUT",
                "message": "Model inference timed out",
            },
        ) from exc

    except httpx.HTTPStatusError as exc:

        raise HTTPException(
            status_code=502,
            detail={
                "error": "MODEL_INFERENCE_FAILED",
                "message": "Model backend returned an error",
            },
        ) from exc

    except httpx.RequestError as exc:

        raise HTTPException(
            status_code=502,
            detail={
                "error": "MODEL_UNREACHABLE",
                "message": "Could not reach model backend",
            },
        ) from exc

    return EmbeddingResponse(
        request_id=request_id,
        model="octen-embed",
        dim=len(embeddings[0]) if embeddings else 0,
        embeddings=embeddings,
    )


@router.post(
    "/clip-embed/embed",
    response_model=EmbeddingResponse,
)
async def embed_image(
    http_request: Request,
    file: UploadFile = File(...),
    normalize: bool = Query(default=True),
):

    request_id = http_request.state.request_id

    if file.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail={
                "error": "UNSUPPORTED_MEDIA_TYPE",
                "message": f"Unsupported content type: {file.content_type}",
            },
        )

    content = await file.read()

    if len(content) > _MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "PAYLOAD_TOO_LARGE",
                "message": "Image exceeds the 10MB limit",
            },
        )

    try:

        embedding = await inference_service.embed_image(
            model_name="clip-embed",
            filename=file.filename or "upload",
            content_type=file.content_type,
            content=content,
            normalize=normalize,
            request_id=request_id,
        )

    except httpx.TimeoutException as exc:

        raise HTTPException(
            status_code=504,
            detail={
                "error": "MODEL_TIMEOUT",
                "message": "Model inference timed out",
            },
        ) from exc

    except httpx.HTTPStatusError as exc:

        raise HTTPException(
            status_code=502,
            detail={
                "error": "MODEL_INFERENCE_FAILED",
                "message": "Model backend returned an error",
            },
        ) from exc

    except httpx.RequestError as exc:

        raise HTTPException(
            status_code=502,
            detail={
                "error": "MODEL_UNREACHABLE",
                "message": "Could not reach model backend",
            },
        ) from exc

    return EmbeddingResponse(
        request_id=request_id,
        model="clip-embed",
        dim=len(embedding),
        embeddings=[embedding],
    )
