import os
from typing import Optional


class Settings:
    # Application
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "documents")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "true").lower() == "true"

    # Qdrant
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")

    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

    # NVIDIA
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_BASE_URL: str = os.getenv(
        "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
    )

    # Processing
    DEFAULT_CHUNK_SIZE: int = int(os.getenv("DEFAULT_CHUNK_SIZE", 1000))
    DEFAULT_EMBEDDING_MODEL: str = os.getenv(
        "DEFAULT_EMBEDDING_MODEL", "nvidia/llama-3.2-nv-embedqa-1b-v2"
    )


settings = Settings()
