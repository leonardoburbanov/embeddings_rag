"""Rank the catalog with one embedding provider."""

from app.domains.catalog.domain.embedder import Embedder
from app.domains.catalog.domain.product import ScoredProduct
from app.domains.catalog.domain.repository import CatalogRepository


async def search_products(
    repository: CatalogRepository,
    embedder: Embedder,
    *,
    text: str | None,
    image: bytes | None,
    mime_type: str | None,
    limit: int = 24,
) -> list[ScoredProduct]:
    """Embed the query and search the vector that belongs to this provider."""
    vector = await embedder.embed_query(text, image, mime_type)
    return await repository.search(vector, embedder.name, limit)
