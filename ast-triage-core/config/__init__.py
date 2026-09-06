"""
config - Application configuration management for AST-Triage.

Provides centralized settings loaded from environment variables
and .env files using Pydantic BaseSettings.
"""
from config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
