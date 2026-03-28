from __future__ import annotations

from types import SimpleNamespace

from app.services.ai.providers.anthropic import AnthropicProvider
from app.services.ai.providers.openai import OpenAIProvider
from app.services.ai.providers.selector import ProviderSelector


class _FakeDB:
    def __init__(self, *responses):
        self._responses = list(responses)

    def scalar(self, _query):  # noqa: ANN001
        if not self._responses:
            return None
        return self._responses.pop(0)


def _provider_model(provider_type: str) -> SimpleNamespace:
    return SimpleNamespace(
        provider_type=provider_type,
        base_url="https://example.test/v1",
        encrypted_api_key=None,
        model="model-x",
        timeout_seconds=12.0,
        max_completion_tokens=900,
        extra_headers_json=None,
    )


def test_selector_prefers_user_provider_over_tenant() -> None:
    user_provider = _provider_model("anthropic")
    tenant_provider = _provider_model("openai")
    db = _FakeDB(user_provider, tenant_provider)
    selector = ProviderSelector(db)
    provider = selector.get_provider(tenant_id=1, user_id=10)
    assert isinstance(provider, AnthropicProvider)


def test_selector_prefers_tenant_when_user_missing() -> None:
    tenant_provider = _provider_model("openai")
    db = _FakeDB(None, tenant_provider)
    selector = ProviderSelector(db)
    provider = selector.get_provider(tenant_id=1, user_id=10)
    assert isinstance(provider, OpenAIProvider)


def test_selector_uses_platform_when_tenant_missing() -> None:
    platform_provider = _provider_model("anthropic")
    db = _FakeDB(None, platform_provider)
    selector = ProviderSelector(db)
    provider = selector.get_provider(tenant_id=1, user_id=None)
    assert isinstance(provider, AnthropicProvider)


def test_selector_falls_back_to_local_settings(monkeypatch) -> None:  # noqa: ANN001
    db = _FakeDB(None, None)
    selector = ProviderSelector(db)
    monkeypatch.setattr("app.services.ai.providers.selector.settings.llm_api_base_url", "http://localhost:4000/v1")
    monkeypatch.setattr("app.services.ai.providers.selector.settings.llm_api_key", "dummy")
    monkeypatch.setattr("app.services.ai.providers.selector.settings.llm_model", "local-model")
    provider = selector.get_provider(tenant_id=99, user_id=None)
    assert isinstance(provider, OpenAIProvider)
    assert provider.base_url == "http://localhost:4000/v1"
    assert provider.model == "local-model"


def test_selector_maps_openai_compatible_to_openai_provider() -> None:
    compatible = _provider_model("openai_compatible")
    db = _FakeDB(compatible)
    selector = ProviderSelector(db)
    provider = selector.get_provider(tenant_id=2, user_id=None)
    assert isinstance(provider, OpenAIProvider)
