"""Cohere embed-v4 client. The SDK call is synchronous, so it runs in a thread."""

import asyncio
from typing import Any

import cohere

from app.config import Settings
from app.domains.catalog.infrastructure.media import check_dimension, content_parts


class CohereEmbedder:
    """Multimodal embeddings from Cohere embed-v4."""

    name = "cohere"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = cohere.ClientV2(api_key=settings.cohere_api_key)

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
        response = await asyncio.to_thread(
            self._client.embed,
            model=self._settings.cohere_embedding_model,
            inputs=[{"content": parts}],
            input_type=input_type,
            embedding_types=["float"],
            output_dimension=self._settings.embedding_dimension,
        )
        vector = _float_vector(response)
        check_dimension(vector, self._settings.embedding_dimension, self.name)
        return vector


def _float_vector(response: Any) -> list[float]:
    """Read the first float embedding from a Cohere v2 response."""
    embeddings = response.embeddings
    floats = getattr(embeddings, "float_", None)
    if floats is None:
        floats = embeddings.float
    return list(floats[0])
