"""Tenant-scoped chatbot service for invoice and comprobante questions."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Sequence

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infra.settings import settings
from app.models.invoice import Invoice
from app.models.tenant import Tenant
from app.portal_client.schemas import ChatAnswerResponse, ChatPreprocessMetadata, ChatQuestionRequest, ChatSource
from app.services.platform_ai import PlatformAIProviderRuntime, load_default_runtime_provider


def _get_tenant_or_404(db: Session, tenant_id: int) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return tenant


def _normalize_question(question: str) -> str:
    normalized = re.sub(r"\s+", " ", (question or "").strip())
    replacements = {
        "dgii": "DGII",
        "odoo": "Odoo",
        "ecf": "e-CF",
        "encf": "eNCF",
        "cual": "cuál",
        "cuantos": "cuántos",
        "ultimo": "último",
        "analisis": "análisis",
        "gramatica": "gramática",
        "ortografia": "ortografía",
        "funcion": "función",
    }
    for source, target in replacements.items():
        normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized, flags=re.IGNORECASE)
    if normalized and normalized[0].isalpha():
        normalized = normalized[0].upper() + normalized[1:]
    return normalized


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", (value or "").lower())


def _currency(value: Decimal) -> str:
    return f"RD${value:,.2f}"


@dataclass(slots=True)
class RankedInvoice:
    invoice: Invoice
    score: int


@dataclass(slots=True)
class ChatPreprocessDecision:
    original_question: str
    normalized_question: str
    normalized_changed: bool
    intent: str
    dispatch_strategy: str
    provider_skipped_to_save_credits: bool
    reasons: list[str]


class TenantChatService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def answer_question(self, *, tenant_id: int, payload: ChatQuestionRequest) -> ChatAnswerResponse:
        if not settings.llm_chat_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Chatbot deshabilitado",
            )

        tenant = _get_tenant_or_404(self.db, tenant_id)
        platform_provider = load_default_runtime_provider(self.db)
        external_provider_available = bool(platform_provider) or settings.llm_provider == "openai_compatible"
        preprocess = self._preprocess_question(payload.question, provider_available=external_provider_available)
        question = preprocess.normalized_question
        invoices = self._load_tenant_invoices(tenant.id)
        ranked = self._rank_invoices(question, invoices)
        explicit_reference = self._extract_explicit_reference(question)
        matched_explicit_reference = self._has_explicit_match(explicit_reference, ranked)
        top_ranked = ranked[: payload.max_sources] if matched_explicit_reference or not explicit_reference else []
        sources = [self._to_source(item.invoice) for item in top_ranked]
        warnings: list[str] = []

        if preprocess.provider_skipped_to_save_credits:
            warnings.append("Consulta operativa resuelta localmente para ahorrar créditos IA.")

        if preprocess.intent == "greeting":
            return ChatAnswerResponse(
                answer=(
                    "Puedo ayudarte con estados, conteos, rechazos, aceptación, comprobantes específicos "
                    "y resúmenes de facturas de tu empresa. Escribe un eNCF, un estado DGII o una pregunta operativa."
                ),
                engine="local",
                tenant_id=tenant.id,
                sources=[],
                warnings=warnings,
                preprocess=self._to_preprocess_metadata(preprocess),
            )

        if preprocess.dispatch_strategy == "local_only":
            answer = self._answer_local(
                tenant=tenant,
                question=question,
                ranked=top_ranked,
                invoices=invoices,
                explicit_reference=explicit_reference,
            )
            engine = "local"
        elif platform_provider:
            try:
                answer = self._answer_with_platform_provider(
                    provider=platform_provider,
                    tenant=tenant,
                    question=question,
                    ranked=top_ranked,
                    invoices=invoices,
                    explicit_reference=explicit_reference,
                )
            except Exception:
                answer = self._answer_local(
                    tenant=tenant,
                    question=question,
                    ranked=top_ranked,
                    invoices=invoices,
                    explicit_reference=explicit_reference,
                )
                warnings.append(f"Fallo el proveedor IA {platform_provider.display_name}; se uso el motor local de respaldo.")
                engine = f"{platform_provider.provider_type}-fallback"
            else:
                engine = platform_provider.provider_type
        elif settings.llm_provider == "openai_compatible":
            try:
                answer = self._answer_with_openai_compatible(
                    tenant=tenant,
                    question=question,
                    ranked=top_ranked,
                    invoices=invoices,
                    explicit_reference=explicit_reference,
                )
            except Exception:
                answer = self._answer_local(
                    tenant=tenant,
                    question=question,
                    ranked=top_ranked,
                    invoices=invoices,
                    explicit_reference=explicit_reference,
                )
                warnings.append("Fallo el proveedor LLM externo; se uso el motor local de respaldo.")
                engine = "local-fallback"
            else:
                engine = settings.llm_provider
        else:
            answer = self._answer_local(
                tenant=tenant,
                question=question,
                ranked=top_ranked,
                invoices=invoices,
                explicit_reference=explicit_reference,
            )
            engine = settings.llm_provider

        return ChatAnswerResponse(
            answer=answer,
            engine=engine,
            tenant_id=tenant.id,
            sources=sources,
            warnings=warnings,
            preprocess=self._to_preprocess_metadata(preprocess),
        )

    def _preprocess_question(self, question: str, *, provider_available: bool) -> ChatPreprocessDecision:
        original = (question or "").strip()
        normalized = _normalize_question(original)
        lowered = normalized.lower()
        explicit_reference = self._extract_explicit_reference(normalized)

        greeting_keywords = ("hola", "buenas", "buenos días", "buen dia", "gracias", "saludos")
        analysis_keywords = (
            "analiza",
            "análisis",
            "explica",
            "recomienda",
            "compara",
            "tendencia",
            "patrón",
            "patron",
            "riesgo",
            "insight",
            "estrategia",
            "causa",
            "por qué",
            "porque",
        )
        operational_keywords = (
            "estado",
            "detalle",
            "detalles",
            "track",
            "último",
            "ultimo",
            "cuántos",
            "cuantos",
            "cantidad",
            "total",
            "resumen",
            "acept",
            "rechaz",
            "contabil",
            "comprobante",
            "factura",
            "emitido",
            "emitida",
        )

        reasons: list[str] = []
        if any(keyword in lowered for keyword in greeting_keywords) and len(_tokenize(lowered)) <= 6:
            intent = "greeting"
        elif any(keyword in lowered for keyword in analysis_keywords):
            intent = "analysis"
        elif explicit_reference or any(keyword in lowered for keyword in operational_keywords):
            intent = "operational_lookup"
        else:
            intent = "open_question"

        if not provider_available:
            dispatch_strategy = "local_only"
            reasons.append("No hay proveedor IA externo disponible; la consulta se resuelve localmente.")
        elif intent in {"greeting", "operational_lookup"}:
            dispatch_strategy = "local_only"
            reasons.append("La consulta puede resolverse con reglas y datos locales antes de consumir créditos.")
        else:
            dispatch_strategy = "provider_preferred"
            reasons.append("La consulta es abierta o analítica y puede beneficiarse del proveedor IA.")

        return ChatPreprocessDecision(
            original_question=original,
            normalized_question=normalized,
            normalized_changed=normalized != original,
            intent=intent,
            dispatch_strategy=dispatch_strategy,
            provider_skipped_to_save_credits=provider_available and dispatch_strategy == "local_only",
            reasons=reasons,
        )

    def _to_preprocess_metadata(self, decision: ChatPreprocessDecision) -> ChatPreprocessMetadata:
        return ChatPreprocessMetadata(
            originalQuestion=decision.original_question,
            normalizedQuestion=decision.normalized_question,
            normalizedChanged=decision.normalized_changed,
            intent=decision.intent,
            dispatchStrategy=decision.dispatch_strategy,
            providerSkippedToSaveCredits=decision.provider_skipped_to_save_credits,
            reasons=decision.reasons,
        )

    def _load_tenant_invoices(self, tenant_id: int) -> list[Invoice]:
        stmt = (
            select(Invoice)
            .where(Invoice.tenant_id == tenant_id)
            .order_by(Invoice.fecha_emision.desc(), Invoice.id.desc())
            .limit(settings.llm_max_context_invoices)
        )
        return list(self.db.scalars(stmt).all())

    def _rank_invoices(self, question: str, invoices: Sequence[Invoice]) -> list[RankedInvoice]:
        question_upper = question.upper()
        question_tokens = set(_tokenize(question))
        question_digits = set(re.findall(r"\d+", question))
        ranked: list[RankedInvoice] = []

        for invoice in invoices:
            score = 0
            if invoice.encf and invoice.encf.upper() in question_upper:
                score += 120
            if invoice.track_id and invoice.track_id.upper() in question_upper:
                score += 100
            if invoice.rnc_receptor and invoice.rnc_receptor in question_digits:
                score += 60

            blob = " ".join(
                filter(
                    None,
                    [
                        invoice.encf,
                        invoice.track_id,
                        invoice.tipo_ecf,
                        invoice.estado_dgii,
                        invoice.rnc_receptor,
                        invoice.asiento_referencia,
                    ],
                )
            )
            blob_tokens = set(_tokenize(blob))
            score += len(question_tokens & blob_tokens) * 8

            if "rechaz" in question.lower() and invoice.estado_dgii.upper().startswith("RECHAZ"):
                score += 20
            if "acept" in question.lower() and invoice.estado_dgii.upper().startswith("ACEPT"):
                score += 20
            if "contabil" in question.lower() and invoice.contabilizado:
                score += 18
            if "ultimo" in question.lower() or "último" in question.lower() or "reciente" in question.lower():
                score += 6

            total_string = f"{Decimal(str(invoice.total)):.2f}".replace(",", "")
            if total_string in question or str(int(Decimal(str(invoice.total)))) in question_digits:
                score += 12

            ranked.append(RankedInvoice(invoice=invoice, score=score))

        ranked.sort(key=lambda item: (item.score, item.invoice.fecha_emision, item.invoice.id), reverse=True)
        if ranked and ranked[0].score == 0:
            return ranked[: min(3, len(ranked))]
        return [item for item in ranked if item.score > 0] or ranked[: min(3, len(ranked))]

    def _answer_local(
        self,
        *,
        tenant: Tenant,
        question: str,
        ranked: Sequence[RankedInvoice],
        invoices: Sequence[Invoice],
        explicit_reference: str | None,
    ) -> str:
        if not invoices:
            return (
                f"No tengo comprobantes registrados para {tenant.name}. "
                "Solo puedo responder con informacion de tu empresa actual."
            )

        if explicit_reference and not ranked:
            return (
                f"No encontre el comprobante o referencia {explicit_reference} dentro de la informacion de {tenant.name}. "
                "Solo puedo acceder a los comprobantes del tenant autenticado."
            )

        summary = self._invoice_summary(tenant.id)
        lowered = question.lower()
        top_invoice = ranked[0].invoice if ranked else None

        if any(token in lowered for token in ("otra empresa", "otros clientes", "otras empresas", "otros tenants")):
            return (
                "Solo tengo acceso a la informacion del tenant autenticado. "
                "No puedo ver ni responder sobre otras empresas o clientes."
            )

        if any(token in lowered for token in ("resumen", "cuantos", "cuántos", "cantidad", "totales", "total de comprobantes")):
            return (
                f"Para {tenant.name} tengo {summary['count']} comprobantes en contexto, "
                f"{summary['accepted']} aceptados, {summary['rejected']} rechazados y "
                f"{summary['other']} en otros estados. El monto acumulado es {_currency(summary['total_amount'])}."
            )

        if "rechaz" in lowered:
            rejected = [item.invoice for item in ranked if item.invoice.estado_dgii.upper().startswith("RECHAZ")]
            if not rejected:
                return "No encontre comprobantes rechazados dentro de la informacion disponible de tu empresa."
            preview = ", ".join(invoice.encf for invoice in rejected[:3])
            return f"Los comprobantes rechazados mas relevantes son: {preview}."

        if "acept" in lowered:
            accepted = [item.invoice for item in ranked if item.invoice.estado_dgii.upper().startswith("ACEPT")]
            if not accepted:
                return "No encontre comprobantes aceptados que coincidan con tu consulta."
            preview = ", ".join(invoice.encf for invoice in accepted[:3])
            return f"Los comprobantes aceptados mas relevantes son: {preview}."

        if "contabil" in lowered:
            contabilizados = [item.invoice for item in ranked if item.invoice.contabilizado]
            if not contabilizados:
                return "No encontre comprobantes contabilizados que coincidan con tu consulta."
            first = contabilizados[0]
            asiento = first.asiento_referencia or "sin referencia contable"
            return f"El comprobante {first.encf} ya fue contabilizado y su referencia es {asiento}."

        if top_invoice:
            total = Decimal(str(top_invoice.total))
            detail = (
                f"El comprobante {top_invoice.encf} esta en estado {top_invoice.estado_dgii}, "
                f"por {_currency(total)}, emitido el {top_invoice.fecha_emision:%Y-%m-%d}."
            )
            if top_invoice.track_id:
                detail += f" Track ID: {top_invoice.track_id}."
            if top_invoice.contabilizado:
                detail += " Ya esta contabilizado."
            else:
                detail += " Aun no figura como contabilizado."
            return detail

        return (
            "No encontre evidencia suficiente dentro de los comprobantes de tu empresa para responder con precision. "
            "Prueba indicando un eNCF, estado DGII o rango de facturas."
        )

    def _answer_with_openai_compatible(
        self,
        *,
        tenant: Tenant,
        question: str,
        ranked: Sequence[RankedInvoice],
        invoices: Sequence[Invoice],
        explicit_reference: str | None,
    ) -> str:
        if not settings.llm_api_base_url or not settings.llm_api_key:
            raise RuntimeError("Proveedor LLM externo no configurado")

        if explicit_reference and not ranked:
            return (
                f"No encontre la referencia {explicit_reference} en los comprobantes del tenant autenticado. "
                "No tengo acceso a otras empresas o clientes."
            )

        context_blocks = [self._context_block(tenant, invoices)]
        if ranked:
            context_blocks.append("Comprobantes mas relevantes:")
            context_blocks.extend(self._invoice_block(item.invoice) for item in ranked)

        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un asistente de facturacion electronica multi-tenant. "
                    "Responde solo con la informacion del tenant autenticado incluida en el contexto. "
                    "Nunca inventes datos, nunca hagas referencias a otras empresas o clientes, "
                    "y si el contexto no alcanza debes decirlo claramente."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Tenant: {tenant.name} (RNC {tenant.rnc})\n"
                    f"Pregunta: {question}\n\n"
                    "Contexto permitido:\n"
                    + "\n".join(context_blocks)
                ),
            },
        ]

        response = httpx.post(
            f"{settings.llm_api_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "temperature": 0.1,
                "max_tokens": settings.llm_max_completion_tokens,
                "messages": messages,
            },
            timeout=settings.llm_timeout_seconds,
        )
        return self._parse_openai_style_response(response)

    def _answer_with_platform_provider(
        self,
        *,
        provider: PlatformAIProviderRuntime,
        tenant: Tenant,
        question: str,
        ranked: Sequence[RankedInvoice],
        invoices: Sequence[Invoice],
        explicit_reference: str | None,
    ) -> str:
        if provider.provider_type in {"openai", "openai_compatible"}:
            return self._answer_with_openai_style_provider(
                provider=provider,
                tenant=tenant,
                question=question,
                ranked=ranked,
                invoices=invoices,
                explicit_reference=explicit_reference,
            )
        if provider.provider_type == "gemini":
            return self._answer_with_gemini_provider(
                provider=provider,
                tenant=tenant,
                question=question,
                ranked=ranked,
                invoices=invoices,
                explicit_reference=explicit_reference,
            )
        raise RuntimeError(f"Proveedor IA no soportado en runtime: {provider.provider_type}")

    def _answer_with_openai_style_provider(
        self,
        *,
        provider: PlatformAIProviderRuntime,
        tenant: Tenant,
        question: str,
        ranked: Sequence[RankedInvoice],
        invoices: Sequence[Invoice],
        explicit_reference: str | None,
    ) -> str:
        if not provider.base_url or not provider.api_key:
            raise RuntimeError("Proveedor OpenAI sin base_url o api_key")
        if explicit_reference and not ranked:
            return (
                f"No encontre la referencia {explicit_reference} en los comprobantes del tenant autenticado. "
                "No tengo acceso a otras empresas o clientes."
            )

        context_blocks = [self._context_block(tenant, invoices)]
        if ranked:
            context_blocks.append("Comprobantes mas relevantes:")
            context_blocks.extend(self._invoice_block(item.invoice) for item in ranked)

        system_prompt = provider.system_prompt or (
            "Eres un asistente de facturacion electronica multi-tenant. "
            "Responde solo con la informacion del tenant autenticado incluida en el contexto. "
            "Nunca inventes datos, nunca hagas referencias a otras empresas o clientes, "
            "y si el contexto no alcanza debes decirlo claramente."
        )
        response = httpx.post(
            self._openai_chat_url(provider.base_url),
            headers={
                "Authorization": f"Bearer {provider.api_key}",
                "Content-Type": "application/json",
                **provider.extra_headers,
            },
            json={
                "model": provider.model,
                "temperature": 0.1,
                "max_tokens": provider.max_completion_tokens,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Tenant: {tenant.name} (RNC {tenant.rnc})\n"
                            f"Pregunta: {question}\n\n"
                            "Contexto permitido:\n"
                            + "\n".join(context_blocks)
                        ),
                    },
                ],
            },
            timeout=provider.timeout_seconds,
        )
        return self._parse_openai_style_response(response)

    def _answer_with_gemini_provider(
        self,
        *,
        provider: PlatformAIProviderRuntime,
        tenant: Tenant,
        question: str,
        ranked: Sequence[RankedInvoice],
        invoices: Sequence[Invoice],
        explicit_reference: str | None,
    ) -> str:
        if not provider.base_url or not provider.api_key:
            raise RuntimeError("Proveedor Gemini sin base_url o api_key")
        if explicit_reference and not ranked:
            return (
                f"No encontre la referencia {explicit_reference} en los comprobantes del tenant autenticado. "
                "No tengo acceso a otras empresas o clientes."
            )

        context_blocks = [self._context_block(tenant, invoices)]
        if ranked:
            context_blocks.append("Comprobantes mas relevantes:")
            context_blocks.extend(self._invoice_block(item.invoice) for item in ranked)

        system_prompt = provider.system_prompt or (
            "Responde solo con informacion del tenant autenticado. "
            "Si la pregunta pide datos de otra empresa o el contexto no alcanza, debes negarte claramente."
        )
        response = httpx.post(
            self._gemini_generate_url(provider.base_url, provider.model),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": provider.api_key,
                **provider.extra_headers,
            },
            json={
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": (
                                    f"Tenant: {tenant.name} (RNC {tenant.rnc})\n"
                                    f"Pregunta: {question}\n\n"
                                    "Contexto permitido:\n"
                                    + "\n".join(context_blocks)
                                )
                            }
                        ],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": provider.max_completion_tokens,
                },
            },
            timeout=provider.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        candidates = payload.get("candidates") or []
        if not candidates:
            raise RuntimeError("Proveedor Gemini sin candidates")
        content = (candidates[0] or {}).get("content") or {}
        parts = content.get("parts") or []
        texts = [part.get("text", "").strip() for part in parts if isinstance(part, dict)]
        answer = "\n".join(text for text in texts if text)
        if not answer:
            raise RuntimeError("Proveedor Gemini sin contenido")
        return answer

    def _parse_openai_style_response(self, response: httpx.Response) -> str:
        response.raise_for_status()
        payload = response.json()
        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError("Proveedor LLM sin choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Proveedor LLM sin contenido")
        return content.strip()

    def _openai_chat_url(self, base_url: str) -> str:
        normalized = base_url.rstrip("/")
        if normalized.endswith("/chat/completions"):
            return normalized
        return f"{normalized}/chat/completions"

    def _gemini_generate_url(self, base_url: str, model: str) -> str:
        normalized = base_url.rstrip("/")
        if normalized.endswith(f"/models/{model}:generateContent"):
            return normalized
        return f"{normalized}/models/{model}:generateContent"

    def _invoice_summary(self, tenant_id: int) -> dict[str, Decimal | int]:
        total_count = self.db.scalar(select(func.count()).where(Invoice.tenant_id == tenant_id)) or 0
        accepted = (
            self.db.scalar(select(func.count()).where(Invoice.tenant_id == tenant_id, Invoice.estado_dgii == "ACEPTADO"))
            or 0
        )
        rejected = (
            self.db.scalar(select(func.count()).where(Invoice.tenant_id == tenant_id, Invoice.estado_dgii == "RECHAZADO"))
            or 0
        )
        total_amount = (
            self.db.scalar(select(func.coalesce(func.sum(Invoice.total), 0)).where(Invoice.tenant_id == tenant_id))
            or Decimal("0")
        )
        return {
            "count": int(total_count),
            "accepted": int(accepted),
            "rejected": int(rejected),
            "other": max(int(total_count) - int(accepted) - int(rejected), 0),
            "total_amount": Decimal(str(total_amount)),
        }

    def _context_block(self, tenant: Tenant, invoices: Sequence[Invoice]) -> str:
        summary = self._invoice_summary(tenant.id)
        latest = invoices[0] if invoices else None
        latest_note = f" Ultimo comprobante: {latest.encf} ({latest.estado_dgii})." if latest else ""
        return (
            f"Empresa: {tenant.name} | RNC: {tenant.rnc} | Ambiente: {tenant.env}. "
            f"Resumen: {summary['count']} comprobantes, {summary['accepted']} aceptados, "
            f"{summary['rejected']} rechazados, monto acumulado {_currency(summary['total_amount'])}."
            f"{latest_note}"
        )

    def _invoice_block(self, invoice: Invoice) -> str:
        return (
            f"- id={invoice.id}, encf={invoice.encf}, tipo={invoice.tipo_ecf}, estado={invoice.estado_dgii}, "
            f"track_id={invoice.track_id or 'N/A'}, total={Decimal(str(invoice.total)):.2f}, "
            f"fecha={invoice.fecha_emision:%Y-%m-%d}, receptor={invoice.rnc_receptor or 'N/A'}, "
            f"contabilizado={'si' if invoice.contabilizado else 'no'}, "
            f"asiento={invoice.asiento_referencia or 'N/A'}"
        )

    def _to_source(self, invoice: Invoice) -> ChatSource:
        total = Decimal(str(invoice.total))
        snippet = (
            f"{invoice.encf}: estado {invoice.estado_dgii}, "
            f"monto {_currency(total)}, fecha {invoice.fecha_emision:%Y-%m-%d}"
        )
        return ChatSource(
            invoice_id=invoice.id,
            encf=invoice.encf,
            track_id=invoice.track_id,
            estado_dgii=invoice.estado_dgii,
            total=total,
            fecha_emision=invoice.fecha_emision,
            snippet=snippet,
        )

    def _extract_explicit_reference(self, question: str) -> str | None:
        patterns = (
            r"\bE[0-9A-Z]{8,20}\b",
            r"\bTRACK[-_A-Z0-9]{4,64}\b",
        )
        question_upper = question.upper()
        for pattern in patterns:
            match = re.search(pattern, question_upper)
            if match:
                return match.group(0)
        return None

    def _has_explicit_match(self, explicit_reference: str | None, ranked: Sequence[RankedInvoice]) -> bool:
        if not explicit_reference:
            return True
        for item in ranked:
            invoice = item.invoice
            if invoice.encf.upper() == explicit_reference:
                return True
            if invoice.track_id and invoice.track_id.upper() == explicit_reference:
                return True
        return False
