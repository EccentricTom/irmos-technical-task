from __future__ import annotations

from json import load
import os
import re
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    db_url: str = os.getenv("DB_URL", "sqlite:///./data/midspan_data.db")
    csv_path: str = os.getenv("CSV_PATH", "./data/midspan_data.csv")
    table_name: str = os.getenv("TABLE_NAME", "midspan_data")
    mode_db: str =  os.getenv("MODE_DB", "replace")

    # debug toggle for endpoint
    enable_debug_endpoint: bool = False

    # api/settings.py -> project root is parent of "api"
    project_root: Path = Path(__file__).resolve().parents[1]

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", v):
            raise ValueError("TABLE_NAME must match [A-Za-z_][A-Za-z0-9_]*")
        return v

    @property
    def is_sqlite(self) -> bool:
        return self.db_url.startswith("sqlite:///")

    @property
    def resolved_db_path(self) -> Path | None:
        if not self.is_sqlite:
            return None
        raw = self.db_url[len("sqlite:///"):]  # keep "///" semantics
        p = Path(raw)
        if not p.is_absolute():
            p = (self.project_root / p).resolve()
        return p

    @property
    def resolved_db_url(self) -> str:
        if not self.is_sqlite:
            return self.db_url
        return f"sqlite:///{self.resolved_db_path.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
