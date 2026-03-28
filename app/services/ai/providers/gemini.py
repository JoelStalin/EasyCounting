"""Google Gemini provider."""
from __future__ import annotations

import time
from typing import Any
import httpx

from app.services.ai.providers.base import BaseLLMProvider, LLMResponse


class GeminiProvider(BaseLLMProvider):
    """Adaptador para Google Gemini."""

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        if not self.base_url:
            self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        # Gemini format transformation
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
        chat_messages = [m for m in messages if m["role"] != "system"]

        contents = []
        for msg in chat_messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        url = f"{self.base_url.rstrip('/')}/models/{self.model}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json",
            **self.extra_headers
        }

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.1),
                "maxOutputTokens": kwargs.get("max_tokens", self.max_tokens),
            }
        }
        if system_msg:
            payload["system_instruction"] = {"parts": [{"text": system_msg}]}

        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        
        end_time = time.perf_counter()
        latency_ms = int((end_time - start_time) * 1000)

        # Gemini response structure
        candidate = data["candidates"][0]
        content = candidate["content"]["parts"][0]["text"].strip()
        usage = data.get("usageMetadata", {})

        return LLMResponse(
            content=content,
            model=data.get("model", self.model or "unknown"),
            provider="gemini",
            usage={
                "input_tokens": usage.get("promptTokenCount", 0),
                "output_tokens": usage.get("candidatesTokenCount", 0),
            },
            latency_ms=latency_ms
        )
