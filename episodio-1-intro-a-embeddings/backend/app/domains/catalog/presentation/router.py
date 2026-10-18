"""Catalog HTTP routes."""

from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.domains.catalog.application.explain_match import (
    ModalityMissing,
    ProductNotFound,
    explain_match,
)
from app.domains.catalog.application.list_products import list_products
from app.domains.catalog.application.search_products import search_products
from app.domains.catalog.presentation.dependencies import EmbeddersDep, RepositoryDep
from app.domains.catalog.presentation.schemas import MatchOut, ProductOut, SearchHitOut

router = APIRouter(tags=["catalog"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


@router.get("/products", response_model=list[ProductOut])
async def get_products(repository: RepositoryDep) -> list[ProductOut]:
    """Return the full catalog. This path does not call an embedding model."""
    products = await list_products(repository)
    return [ProductOut.model_validate(product.to_dict()) for product in products]


@router.post("/search", response_model=list[SearchHitOut])
async def search(
    repository: RepositoryDep,
    embedders: EmbeddersDep,
    provider: Annotated[Literal["gemini", "cohere"], Form()],
    query: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> list[SearchHitOut]:
    """Rank the catalog with text, an image, or both, using the chosen provider."""
    text = query.strip() if query else None
    image_bytes, mime_type = await _read_image(image)
    if not text and image_bytes is None:
        raise HTTPException(status_code=400, detail="Escribe un texto o adjunta una imagen.")
    embedder = embedders.get(provider)
    if embedder is None:
        raise HTTPException(status_code=400, detail="Proveedor desconocido.")
    try:
        hits = await search_products(
            repository,
            embedder,
            text=text,
            image=image_bytes,
            mime_type=mime_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="No se pudo calcular el embedding.") from exc
    return [
        SearchHitOut.model_validate({**hit.product.to_dict(), "score": hit.score})
        for hit in hits
    ]


@router.post("/products/{product_id}/match", response_model=MatchOut)
async def match_product(
    product_id: str,
    repository: RepositoryDep,
    embedders: EmbeddersDep,
    provider: Annotated[Literal["gemini", "cohere"], Form()],
    query: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> MatchOut:
    """Say whether this product matched on its text or its photo, and project both."""
    text = query.strip() if query else None
    image_bytes, mime_type = await _read_image(image)
    if not text and image_bytes is None:
        raise HTTPException(status_code=400, detail="Escribe un texto o adjunta una imagen.")
    embedder = embedders.get(provider)
    if embedder is None:
        raise HTTPException(status_code=400, detail="Proveedor desconocido.")
    try:
        explanation = await explain_match(
            repository,
            embedder,
            product_id,
            text=text,
            image=image_bytes,
            mime_type=mime_type,
        )
    except ProductNotFound:
        raise HTTPException(status_code=404, detail="Ese producto no está en el catálogo.") from None
    except ModalityMissing:
        raise HTTPException(
            status_code=409,
            detail="Este producto no tiene embeddings de texto e imagen. Vuelve a cargar el catálogo.",
        ) from None
    except Exception as exc:
        raise HTTPException(status_code=502, detail="No se pudo calcular el embedding.") from exc
    return MatchOut(
        matched=explanation.matched,  # type: ignore[arg-type]
        text_score=explanation.text_score,
        image_score=explanation.image_score,
        points=[
            {
                "label": point.label,
                "x": point.x,
                "y": point.y,
                "z": point.z,
                "role": point.role,
            }
            for point in explanation.points
        ],
    )


async def _read_image(image: UploadFile | None) -> tuple[bytes | None, str | None]:
    """Read an optional upload and reject unsupported or oversized files."""
    if image is None or not image.filename:
        return None, None
    raw = await image.read()
    if not raw:
        return None, None
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="La imagen supera 5 MB.")
    mime_type = (image.content_type or "image/jpeg").split(";")[0].strip().lower()
    if mime_type == "image/jpg":
        mime_type = "image/jpeg"
    if mime_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Formato de imagen no soportado.")
    return raw, mime_type
