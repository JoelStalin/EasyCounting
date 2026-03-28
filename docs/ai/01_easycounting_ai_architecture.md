# EasyCounting AI Architecture (Phase Continuation)

## Scope
- Multi-provider chat orchestration for tenant portal.
- Long-term memory persistence (semantic + conversation).
- Tenant/provider hierarchy and safe local fallback.
- Operational endpoints for chat memory management.

## Current Provider Resolution
1. User default provider (`user_ai_providers`).
2. Tenant default provider (`tenant_ai_providers`).
3. Platform default provider (`platform_ai_providers`).
4. Local OpenAI-compatible fallback from settings.

Supported provider types:
- `openai`
- `gemini`
- `anthropic`
- `openai_compatible`

## Components
- `app/services/ai/orchestrator.py`: end-to-end orchestration.
- `app/services/ai/providers/selector.py`: provider hierarchy and adapter factory.
- `app/services/ai/memory_service.py`: embeddings + semantic memory retrieval with safe fallback.
- `app/services/ai/context_builder.py`: RAG context from invoices + memories.
- `app/services/ai/conversation_service.py`: session/message persistence.

## Data Model
- `chat_sessions`
- `chat_messages`
- `semantic_memories`
- `tenant_ai_providers`
- `user_ai_providers`

## API Additions (Tenant Client)
- `GET /api/v1/cliente/chat/memory`
- `GET /api/v1/cliente/chat/memory/search?q=...`
- `POST /api/v1/cliente/chat/memory`
- `PATCH /api/v1/cliente/chat/memory/{memory_id}`
- `DELETE /api/v1/cliente/chat/memory/{memory_id}`

All queries are tenant-filtered and user-scoped where applicable.

## API Additions (Admin)
- `GET /api/v1/admin/users/{user_id}/ai-providers`
- `POST /api/v1/admin/users/{user_id}/ai-providers`
- `PUT /api/v1/admin/users/{user_id}/ai-providers/{provider_id}`
- `DELETE /api/v1/admin/users/{user_id}/ai-providers/{provider_id}`

## Reliability Behavior
- If external provider fails, tenant chat falls back to local deterministic response (`engine=local_fallback`).
- Semantic search gracefully degrades to text search when vector operation is unavailable.

## Checkpoint
- Unit tests passing:
  - `app/tests/unit/test_ai_provider_selector.py`
  - legacy unit tests for security/sign/ecf.
- E2E previously green for admin/client/seller + odoo integration.
