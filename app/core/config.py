"""Compatibility wrapper for legacy settings import path."""
from __future__ import annotations

from app.infra.settings import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]
