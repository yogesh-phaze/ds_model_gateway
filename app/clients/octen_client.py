import httpx

from app.config import ModelConfig, settings
from app.schemas.embedding import TextEmbeddingRequest


class OctenEmbedClient:
    """Client for octen-embed-service (llama-server --embedding),
    OpenAI-compatible /v1/embeddings, bearer-token authenticated.
    """

    async def embed(
        self,
        model: ModelConfig,
        request: TextEmbeddingRequest,
    ) -> list[list[float]]:

        url = f"{model.base_url}/v1/embeddings"

        headers = {}
        if settings.OCTEN_EMBED_API_KEY:
            headers["Authorization"] = f"Bearer {settings.OCTEN_EMBED_API_KEY}"

        timeout = httpx.Timeout(
            timeout=model.timeout_seconds,
            connect=5.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:

            response = await client.post(
                url,
                json={"input": request.input},
                headers=headers,
            )

            response.raise_for_status()

            payload = response.json()

        ordered = sorted(
            payload["data"],
            key=lambda item: item.get("index", 0),
        )

        return [item["embedding"] for item in ordered]
