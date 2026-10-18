"""Runtime settings loaded from the environment."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """API keys, Qdrant, and embedding model names."""

    openrouter_api_key: str = ""
    cohere_api_key: str = ""
    qdrant_url: str = "http://localhost:6333"
    gemini_embedding_model: str = "google/gemini-embedding-2"
    cohere_embedding_model: str = "embed-v4.0"
    embedding_dimension: int = 1536
    collection_name: str = "glasses"
    cors_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")
