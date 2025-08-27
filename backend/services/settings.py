from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Storage directories
    UPLOAD_DIR: str = "./uploads"
    STORE_DIR: str = "./local_store"
    CHROMA_DIR: str = "./chroma"

    # Dropbox
    DROPBOX_ACCESS_TOKEN: str | None = (
        None  # For dev; prefer refresh token flow in prod
    )

    class Config:
        env_file = ".env"


settings = Settings()
