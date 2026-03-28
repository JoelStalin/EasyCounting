"""Base LLM provider abstraction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: dict[str, int] | None = None
    latency_ms: int | None = None


class BaseLLMProvider(ABC):
    """Interfaz base para todos los proveedores de LLM."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        max_tokens: int = 1000,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.extra_headers = extra_headers or {}

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        """Envía una consulta al modelo y devuelve una respuesta estructurada."""
        pass
