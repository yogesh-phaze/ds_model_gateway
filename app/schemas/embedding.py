from pydantic import BaseModel, Field, field_validator

MAX_TEXT_LENGTH = 8_000
MAX_BATCH_SIZE = 100


class TextEmbeddingRequest(BaseModel):
    """Request for the octen-embed backend. Accepts a single string or a
    batch, matching the OpenAI-style /v1/embeddings convention.
    """

    input: list[str] = Field(min_length=1, max_length=MAX_BATCH_SIZE)

    @field_validator("input", mode="before")
    @classmethod
    def _coerce_single_string(cls, value):
        if isinstance(value, str):
            return [value]
        return value

    @field_validator("input")
    @classmethod
    def _validate_items(cls, value: list[str]) -> list[str]:
        for item in value:
            if not item.strip():
                raise ValueError("input strings must not be empty")
            if len(item) > MAX_TEXT_LENGTH:
                raise ValueError(
                    f"input strings must be at most {MAX_TEXT_LENGTH} characters"
                )
        return value


class EmbeddingResponse(BaseModel):
    request_id: str
    model: str
    dim: int
    embeddings: list[list[float]]
