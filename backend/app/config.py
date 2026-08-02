from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BACKEND_")

    database_path: Path = BACKEND_DIR / "data" / "app.db"
    seed_data_dir: Path = BACKEND_DIR / "seed_data"
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
