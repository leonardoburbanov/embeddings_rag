"""OpenRouter client for Gemini Embedding 2."""

import httpx

from app.config import Settings
from app.domains.catalog.infrastructure.media import check_dimension, content_parts


class GeminiEmbedder:
    """Multimodal embeddings through OpenRouter's embeddings endpoint."""

    name = "gemini"

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client

    async def embed_document(self, text: str, image: bytes, mime_type: str) -> list[float]:
        """Embed a product photo fused with its catalog text."""
        return await self._embed(text, image, mime_type, "search_document")

    async def embed_document_text(self, text: str) -> list[float]:
        """Embed only the catalog text, using the document input type."""
        return await self._embed(text, None, None, "search_document")

    async def embed_document_image(self, image: bytes, mime_type: str) -> list[float]:
        """Embed only the product photo, using the document input type."""
        return await self._embed(None, image, mime_type, "search_document")

    async def embed_query(
        self,
        text: str | None,
        image: bytes | None,
        mime_type: str | None,
    ) -> list[float]:
        """Embed a text query, an uploaded image, or both."""
        return await self._embed(text, image, mime_type, "search_query")

    async def _embed(
        self,
        text: str | None,
        image: bytes | None,
        mime_type: str | None,
        input_type: str,
    ) -> list[float]:
        parts = content_parts(text, image, mime_type)
        response = await self._client.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={"Authorization": f"Bearer {self._settings.openrouter_api_key}"},
            json={
                "model": self._settings.gemini_embedding_model,
                "input": [{"content": parts}],
                "dimensions": self._settings.embedding_dimension,
                "encoding_format": "float",
                "input_type": input_type,
            },
        )
        if response.status_code >= 400:
            detail = response.text[:300]
            raise RuntimeError(f"OpenRouter embeddings failed ({response.status_code}): {detail}")
        vector = response.json()["data"][0]["embedding"]
        check_dimension(vector, self._settings.embedding_dimension, self.name)
        return vector
