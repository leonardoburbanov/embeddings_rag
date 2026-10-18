"""FastAPI application wiring."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import AsyncQdrantClient

from app.config import Settings
from app.domains.catalog.infrastructure.cohere_embedder import CohereEmbedder
from app.domains.catalog.infrastructure.gemini_embedder import GeminiEmbedder
from app.domains.catalog.infrastructure.qdrant_catalog import QdrantCatalog
from app.domains.catalog.presentation.router import router
from app.ssl import use_system_certificates

use_system_certificates()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Open the HTTP and Qdrant clients for the process lifetime."""
    settings = Settings()
    http = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
    qdrant = AsyncQdrantClient(url=settings.qdrant_url)
    app.state.repository = QdrantCatalog(qdrant, settings.collection_name, settings.embedding_dimension)
    app.state.embedders = {
        "gemini": GeminiEmbedder(settings, http),
        "cohere": CohereEmbedder(settings),
    }
    yield
    await http.aclose()
    await qdrant.close()


def create_app() -> FastAPI:
    """Build the Lente API."""
    settings = Settings()
    app = FastAPI(title="Lente", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api")
    return app


app = create_app()
