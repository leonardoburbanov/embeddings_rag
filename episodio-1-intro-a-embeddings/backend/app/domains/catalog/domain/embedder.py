"""Port for a multimodal embedding provider."""

from typing import Protocol


class Embedder(Protocol):
    """Turns text, an image, or both into one vector in a single space."""

    name: str

    async def embed_document(self, text: str, image: bytes, mime_type: str) -> list[float]:
        """Embed a catalog item. Uses the provider's document input type."""

    async def embed_query(
        self,
        text: str | None,
        image: bytes | None,
        mime_type: str | None,
    ) -> list[float]:
        """Embed a search query. Uses the provider's query input type."""
