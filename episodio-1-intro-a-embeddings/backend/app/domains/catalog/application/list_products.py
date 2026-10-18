"""List the full catalog without calling an embedding model."""

from app.domains.catalog.domain.product import Product
from app.domains.catalog.domain.repository import CatalogRepository


async def list_products(repository: CatalogRepository) -> list[Product]:
    """Return every product currently stored in Qdrant."""
    return await repository.list_products()
