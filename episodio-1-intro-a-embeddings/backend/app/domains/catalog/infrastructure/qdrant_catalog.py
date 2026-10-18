"""Qdrant collection with one named vector per embedding provider."""

import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from app.domains.catalog.domain.product import ModalitySpace, Product, ScoredProduct, StoredProduct

VECTOR_NAMES = ("gemini", "cohere")
_NAMESPACE = uuid.UUID("8d8b5b1e-6c3a-4f0e-9a1d-3c2b7e4f5a60")


class QdrantCatalog:
    """Stores glasses as points. Gemini and Cohere vectors live side by side."""

    def __init__(self, client: AsyncQdrantClient, collection_name: str, dimension: int) -> None:
        self._client = client
        self._collection = collection_name
        self._dimension = dimension

    async def list_products(self) -> list[Product]:
        """Scroll the collection and return products ordered by name."""
        if not await self._client.collection_exists(self._collection):
            return []
        products: list[Product] = []
        offset = None
        while True:
            points, offset = await self._client.scroll(
                collection_name=self._collection,
                limit=64,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            products.extend(_product_from_payload(point.payload or {}) for point in points)
            if offset is None:
                break
        products.sort(key=lambda product: product.name)
        return products

    async def search(self, vector: list[float], vector_name: str, limit: int) -> list[ScoredProduct]:
        """Query one named vector. Score is cosine similarity."""
        if vector_name not in VECTOR_NAMES:
            raise ValueError(f"Unknown vector '{vector_name}'.")
        if not await self._client.collection_exists(self._collection):
            return []
        result = await self._client.query_points(
            collection_name=self._collection,
            query=vector,
            using=vector_name,
            limit=limit,
            with_payload=True,
        )
        return [
            ScoredProduct(product=_product_from_payload(point.payload or {}), score=point.score or 0.0)
            for point in result.points
        ]

    async def replace_all(self, items: list[StoredProduct]) -> None:
        """Recreate the collection and upsert both vectors for every product."""
        if await self._client.collection_exists(self._collection):
            await self._client.delete_collection(self._collection)
        await self._client.create_collection(
            collection_name=self._collection,
            vectors_config={
                name: models.VectorParams(size=self._dimension, distance=models.Distance.COSINE)
                for name in VECTOR_NAMES
            },
        )
        if not items:
            return
        await self._client.upsert(
            collection_name=self._collection,
            points=[_point(item) for item in items],
            wait=True,
        )

    async def modality_space(self, product_id: str, provider: str) -> ModalitySpace | None:
        """Read one product's text and image vectors and the other fused vectors."""
        if provider not in VECTOR_NAMES:
            raise ValueError(f"Unknown vector '{provider}'.")
        if not await self._client.collection_exists(self._collection):
            return None
        text_key = f"{provider}_text"
        image_key = f"{provider}_image"
        text: list[float] | None = None
        image: list[float] | None = None
        found = False
        context: list[tuple[str, list[float]]] = []
        offset = None
        while True:
            points, offset = await self._client.scroll(
                collection_name=self._collection,
                limit=64,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )
            for point in points:
                payload = point.payload or {}
                name = str(payload.get("name", ""))
                if str(payload.get("id")) == product_id:
                    found = True
                    text = _payload_vector(payload.get(text_key))
                    image = _payload_vector(payload.get(image_key))
                    continue
                context.append((name, _named_vector(point.vector, provider)))
            if offset is None:
                break
        if not found:
            return None
        return ModalitySpace(text=text, image=image, context=context)


def _point(item: StoredProduct) -> models.PointStruct:
    """Build a Qdrant point. The id is a stable uuid derived from the product slug."""
    return models.PointStruct(
        id=str(uuid.uuid5(_NAMESPACE, item.product.id)),
        vector={"gemini": item.gemini, "cohere": item.cohere},
        payload={
            **item.product.to_dict(),
            "gemini_text": item.gemini_text,
            "gemini_image": item.gemini_image,
            "cohere_text": item.cohere_text,
            "cohere_image": item.cohere_image,
        },
    )


def _payload_vector(value: object) -> list[float] | None:
    """Return a stored vector, or None when this catalog was seeded without one."""
    if not isinstance(value, list) or not value:
        return None
    return [float(item) for item in value]


def _named_vector(vector: object, name: str) -> list[float]:
    """Read one named vector from a Qdrant point."""
    if not isinstance(vector, dict) or name not in vector:
        raise RuntimeError(f"Missing named vector '{name}'.")
    values = vector[name]
    if hasattr(values, "tolist"):
        values = values.tolist()
    return [float(item) for item in values]


def _product_from_payload(payload: dict[str, object]) -> Product:
    """Rebuild a product from the stored payload."""
    return Product(
        id=str(payload["id"]),
        name=str(payload["name"]),
        category=str(payload["category"]),
        price=float(payload["price"]),  # type: ignore[arg-type]
        description=str(payload["description"]),
        image_url=str(payload["image_url"]),
    )
