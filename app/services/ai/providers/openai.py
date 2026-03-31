"""OpenAI-style provider."""
from __future__ import annotations

import time
from typing import Any
import httpx

from app.services.ai.providers.base import BaseLLMProvider, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """Adaptador para OpenAI y endpoints compatibles."""

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        # Default to official OpenAI endpoint when no base_url is configured
        base_url = (self.base_url or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            **self.extra_headers
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        
        end_time = time.perf_counter()
        latency_ms = int((end_time - start_time) * 1000)

        choice = data["choices"][0]["message"]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["content"].strip(),
            model=data.get("model", self.model or "unknown"),
            provider="openai",
            usage={
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            },
            latency_ms=latency_ms
        )
