"""Request-scoped access to the catalog repository and embedders."""

from typing import Annotated

from fastapi import Depends, Request

from app.domains.catalog.domain.embedder import Embedder
from app.domains.catalog.infrastructure.qdrant_catalog import QdrantCatalog


def get_repository(request: Request) -> QdrantCatalog:
    """Return the Qdrant catalog created at startup."""
    return request.app.state.repository


def get_embedders(request: Request) -> dict[str, Embedder]:
    """Return embedders keyed by provider name."""
    return request.app.state.embedders


RepositoryDep = Annotated[QdrantCatalog, Depends(get_repository)]
EmbeddersDep = Annotated[dict[str, Embedder], Depends(get_embedders)]
