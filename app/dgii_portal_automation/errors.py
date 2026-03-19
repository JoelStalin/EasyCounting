"""Typed exceptions for DGII portal automation."""

from __future__ import annotations


class DGIIAutomationError(RuntimeError):
    """Base error for the automation package."""


class DGIIConfigurationError(DGIIAutomationError):
    """Configuration or dependency error."""


class DGIIAuthenticationError(DGIIAutomationError):
    """Authentication failed or could not be completed."""


class DGIISessionError(DGIIAutomationError):
    """Session validation or refresh failed."""


class DGIINavigationError(DGIIAutomationError):
    """Navigation flow could not be resolved safely."""


class DGIIExtractionError(DGIIAutomationError):
    """Structured extraction failed."""


class DGIIDownloadError(DGIIAutomationError):
    """A download failed validation or could not complete."""


class DGIIReportingError(DGIIAutomationError):
    """Report generation error."""


class DGIISensitiveActionBlockedError(DGIIAutomationError):
    """A sensitive action was blocked in read-only mode."""


class DGIIHumanActionRequired(DGIIAutomationError):
    """Human confirmation or challenge handling is required."""
