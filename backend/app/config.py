from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BACKEND_",
        env_file=BACKEND_DIR.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_path: Path = BACKEND_DIR / "data" / "app.db"
    seed_data_dir: Path = BACKEND_DIR / "seed_data"
    cors_origins: list[str] = ["http://localhost:5173"]
    openrouter_api_key: str | None = Field(
        default=None, validation_alias="OPENROUTER_API_KEY"
    )


settings = Settings()
