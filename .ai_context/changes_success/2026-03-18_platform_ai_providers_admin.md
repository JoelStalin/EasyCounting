# Platform AI Providers Admin - 2026-03-18

## Objective

Add a superroot-only platform admin panel to manage cloud AI providers such as ChatGPT/OpenAI and Gemini, with encrypted API key storage and runtime integration for the tenant chatbot.

## Backend

- Added platform-wide model: `app/models/platform_ai.py`
- Added encrypted provider helpers: `app/services/platform_ai.py`
- Added admin schemas and endpoints:
  - `GET /api/v1/admin/ai-providers`
  - `POST /api/v1/admin/ai-providers`
  - `PUT /api/v1/admin/ai-providers/{provider_id}`
  - `DELETE /api/v1/admin/ai-providers/{provider_id}`
- Enforced access to these endpoints for role `platform_superroot`
- Extended auth permission mapping with `PLATFORM_AI_PROVIDER_MANAGE`
- Connected the tenant chatbot to the enabled default provider when present

## Frontend

- Added admin API client: `frontend/apps/admin-portal/src/api/ai-providers.ts`
- Added page: `frontend/apps/admin-portal/src/pages/AIProviders.tsx`
- Added route: `/ai-providers`
- Added navigation entry `Agentes IA`

## Security behavior

- API keys are stored encrypted, not returned in plaintext
- The admin API only returns:
  - `apiKeyConfigured`
  - `apiKeyMasked`
- UI supports key rotation and key clearing without re-exposing the previous secret

## Runtime behavior

- Default configured provider is used by `TenantChatService`
- Supported runtime providers in this change:
  - `openai`
  - `openai_compatible`
  - `gemini`
- Failing cloud providers fall back to the local rules-based engine

## Verification

- `.\.venv\Scripts\python -m pytest tests/test_admin_ai_providers.py tests/test_admin_accounting.py tests/test_client_chat.py -q`
- Result: `9 passed in 2.38s`
- `.\.venv\Scripts\python -m compileall app`
- Result: `OK`

## Limitation

- `node` is not available in `PATH` on this host, so the admin frontend was updated at source level but not rebuilt into deployable artifacts in this turn.
