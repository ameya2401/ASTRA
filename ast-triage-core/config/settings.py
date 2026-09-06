"""
config/settings.py - Pydantic BaseSettings for AST-Triage runtime configuration.

Loads configuration from environment variables and a .env file.
All settings have sensible defaults for local development with SQLite.

Usage:
    from config.settings import get_settings
    settings = get_settings()
    print(settings.DATABASE_URL)
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the AST-Triage application.

    All values can be overridden via environment variables or a .env file
    in the project root directory.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ---- GitHub Integration ----
    GITHUB_TOKEN: str = ""
    GITHUB_WEBHOOK_SECRET: str = ""

    # ---- Database ----
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/ast_triage.db"

    # ---- ML Model Configuration ----
    MODEL_CHECKPOINT_DIR: str = "./models"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # ---- Risk Thresholds ----
    # Calibrated probability thresholds for risk tier classification.
    # LOW:    risk_score < LOW_RISK_THRESHOLD
    # MEDIUM: LOW_RISK_THRESHOLD <= risk_score < HIGH_RISK_THRESHOLD
    # HIGH:   risk_score >= HIGH_RISK_THRESHOLD
    LOW_RISK_THRESHOLD: float = 0.25
    HIGH_RISK_THRESHOLD: float = 0.65

    # ---- Application ----
    APP_NAME: str = "AST-Triage"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached singleton instance of Settings.

    Using lru_cache ensures the .env file is read only once
    and the same Settings object is reused across the application.
    """
    return Settings()
