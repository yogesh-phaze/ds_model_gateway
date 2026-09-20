import httpx

from app.config import ModelConfig


class ClipEmbedClient:
    """Client for the clip-embed service: POST /embed with a
    multipart image upload, returns a single CLIP embedding vector.
    """

    async def embed_image(
        self,
        model: ModelConfig,
        filename: str,
        content_type: str,
        content: bytes,
        normalize: bool,
    ) -> list[float]:

        url = f"{model.base_url}/embed"

        timeout = httpx.Timeout(
            timeout=model.timeout_seconds,
            connect=5.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:

            response = await client.post(
                url,
                params={"normalize": normalize},
                files={"file": (filename, content, content_type)},
            )

            response.raise_for_status()

            payload = response.json()

        return payload["embedding"]
