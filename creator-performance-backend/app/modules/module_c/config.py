from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MODULE_C_", env_file=BACKEND_ROOT / ".env", extra="ignore")
    training_table: Path = Path("../data-collector/data/training_table.csv")
    collector_root: Path = Path("../data-collector")
    artifacts: Path = Path("artifacts/module_c")
    clip_model: str = "openai/clip-vit-base-patch32"
    clip_revision: str = "main"
    device: Literal["auto", "cpu", "cuda"] = "auto"
    batch_size: int = Field(default=32, ge=1, le=256)
    ocr_enabled: bool = True
    writer: Literal["rules", "gemini"] = "rules"
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY", repr=False)
    gemini_model: str = "gemini-3.5-flash-lite"
    writer_timeout_seconds: float = Field(default=8, gt=0, le=30)
    gemini_requests_per_minute: int = Field(default=2, ge=0)
    gemini_requests_per_day: int = Field(default=20, ge=0)
    max_upload_bytes: int = 10 * 1024 * 1024
    max_image_pixels: int = 25_000_000

    def resolved(self, path: Path) -> Path:
        return (BACKEND_ROOT / path).resolve() if not path.is_absolute() else path.resolve()

    @property
    def artifact_dir(self) -> Path:
        return self.resolved(self.artifacts)


@lru_cache
def get_settings() -> Settings:
    return Settings()
