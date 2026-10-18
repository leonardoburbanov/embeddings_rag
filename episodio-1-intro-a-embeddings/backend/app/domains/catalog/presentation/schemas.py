"""HTTP schemas for the catalog API."""

from typing import Literal

from pydantic import BaseModel, Field


class ProductOut(BaseModel):
    """A glasses product returned to the storefront."""

    id: str
    name: str
    category: str
    price: float
    description: str
    image_url: str


class SearchHitOut(ProductOut):
    """A product ranked by the selected embedding provider."""

    score: float = Field(description="Cosine similarity from the selected provider.")


class MatchPointOut(BaseModel):
    """A catalog or query vector after PCA."""

    label: str
    x: float
    y: float
    z: float
    role: Literal["query", "text", "image", "catalog"]


class MatchOut(BaseModel):
    """Which of the product's embeddings the query landed closer to."""

    matched: Literal["text", "image"]
    text_score: float
    image_score: float
    points: list[MatchPointOut]
