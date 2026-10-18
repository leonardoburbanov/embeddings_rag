"""Product entity and the text that gets fused into each embedding."""

from dataclasses import asdict, dataclass

CATEGORY_LABELS: dict[str, str] = {
    "gafas": "gafas de sol",
    "armazones": "armazones",
}


@dataclass(frozen=True)
class Product:
    """A glasses product stored as a Qdrant payload."""

    id: str
    name: str
    category: str
    price: float
    description: str
    image_url: str

    def to_dict(self) -> dict[str, str | float]:
        """Return a JSON-ready mapping of the product fields."""
        return asdict(self)


@dataclass(frozen=True)
class ScoredProduct:
    """A product plus the similarity score from the active provider."""

    product: Product
    score: float


@dataclass(frozen=True)
class StoredProduct:
    """A product ready to upsert, with fused, text, and image vectors per provider."""

    product: Product
    gemini: list[float]
    cohere: list[float]
    gemini_text: list[float]
    gemini_image: list[float]
    cohere_text: list[float]
    cohere_image: list[float]


@dataclass(frozen=True)
class ModalitySpace:
    """One product's text and image vectors, plus the other fused catalog vectors."""

    text: list[float] | None
    image: list[float] | None
    context: list[tuple[str, list[float]]]


def document_text(product: Product) -> str:
    """Build the short text fused with the product photo at index time."""
    label = CATEGORY_LABELS.get(product.category, product.category)
    return f"{product.name}. {label}. {product.description}"
