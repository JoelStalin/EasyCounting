"""Anthropic (Claude) provider."""
from __future__ import annotations

import time
from typing import Any
import httpx

from app.services.ai.providers.base import BaseLLMProvider, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """Adaptador para Anthropic Claude."""

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        # Anthropic doesn't use standard 'system' role in messages list in the same way as OpenAI
        # for some API versions, but for Messages API we should follow their structure.
        # We assume the caller provides a list of messages.
        
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
        chat_messages = [m for m in messages if m["role"] != "system"]

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key or "",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
            **self.extra_headers
        }

        payload = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "messages": chat_messages,
            "temperature": kwargs.get("temperature", 0.1),
        }
        if system_msg:
            payload["system"] = system_msg

        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        
        end_time = time.perf_counter()
        latency_ms = int((end_time - start_time) * 1000)

        content = data["content"][0]["text"].strip()
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=data.get("model", self.model or "unknown"),
            provider="anthropic",
            usage={
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            },
            latency_ms=latency_ms
        )
