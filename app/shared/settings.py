"""Backwards compatible access point for application settings."""

from app.infra.settings import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]
