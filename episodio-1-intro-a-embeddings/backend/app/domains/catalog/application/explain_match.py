"""Explain whether a query landed closer to a product's text or its photo."""

from dataclasses import dataclass

from app.domains.catalog.domain.embedder import Embedder
from app.domains.catalog.domain.pca import cosine, project
from app.domains.catalog.domain.repository import CatalogRepository


class ProductNotFound(LookupError):
    """The clicked product is not in the collection."""


class ModalityMissing(ValueError):
    """The product was stored before text and image vectors were saved."""


@dataclass(frozen=True)
class MatchPoint:
    """One point in the PCA plot."""

    label: str
    x: float
    y: float
    z: float
    role: str


@dataclass(frozen=True)
class MatchExplanation:
    """Which product embedding won, both scores, and the 3D projection."""

    matched: str
    text_score: float
    image_score: float
    points: list[MatchPoint]


async def explain_match(
    repository: CatalogRepository,
    embedder: Embedder,
    product_id: str,
    text: str | None,
    image: bytes | None,
    mime_type: str | None,
) -> MatchExplanation:
    """Embed the query and compare it with the product's text and image vectors."""
    space = await repository.modality_space(product_id, embedder.name)
    if space is None:
        raise ProductNotFound(product_id)
    if space.text is None or space.image is None:
        raise ModalityMissing(product_id)
    query = await embedder.embed_query(text, image, mime_type)
    text_score = cosine(query, space.text)
    image_score = cosine(query, space.image)
    matched = "text" if text_score >= image_score else "image"
    rows = [query, space.text, space.image]
    labels = [("Consulta", "query"), ("Texto", "text"), ("Imagen", "image")]
    for name, vector in space.context:
        rows.append(vector)
        labels.append((name, "catalog"))
    coords = project(rows)
    points = [
        MatchPoint(label=label, x=coord[0], y=coord[1], z=coord[2], role=role)
        for (label, role), coord in zip(labels, coords, strict=True)
    ]
    return MatchExplanation(
        matched=matched,
        text_score=text_score,
        image_score=image_score,
        points=points,
    )
