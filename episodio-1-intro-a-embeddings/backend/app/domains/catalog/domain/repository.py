"""Port for the product vector store."""

from typing import Protocol

from app.domains.catalog.domain.product import ModalitySpace, Product, ScoredProduct, StoredProduct


class CatalogRepository(Protocol):
    """Reads and replaces the glasses collection."""

    async def list_products(self) -> list[Product]:
        """Return every stored product, ordered by name."""

    async def search(self, vector: list[float], vector_name: str, limit: int) -> list[ScoredProduct]:
        """Rank products by similarity on the named vector."""

    async def replace_all(self, items: list[StoredProduct]) -> None:
        """Drop the collection and insert these products."""

    async def modality_space(self, product_id: str, provider: str) -> ModalitySpace | None:
        """Return text and image vectors for one product, and the other fused vectors."""
