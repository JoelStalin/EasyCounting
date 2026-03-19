from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re

from app.chat_memory.models import ChatTurn, ConversationSession, ConversationSource, PromptRecord
from app.chat_memory.normalize import correct_spanish_text, split_sentences, to_ai_friendly_prompt
from app.chat_memory.redact import redact_text


NOISE_PROMPTS = {"ok", "dale", "listo", "gracias", "continua", "continúa", "perfecto", "sigue"}
STATUS_PRIORITY = {"blocked": 4, "open": 3, "partial": 2, "resolved": 1, "informational": 0}
FILE_PATTERN = re.compile(
    r"`([^`]+\.(?:py|md|ts|tsx|js|json|yml|yaml|ps1|sh|txt|html|csv|xlsx))`|"
    r"([A-Za-z]:\\[^\s]+?\.(?:py|md|ts|tsx|js|json|yml|yaml|ps1|sh|txt|html|csv|xlsx))|"
    r"((?:app|docs|tests|scripts|frontend|integration|ops|infra|e2e|\.ai_context)/[^\s`]+?\.(?:py|md|ts|tsx|js|json|yml|yaml|ps1|sh|txt|html|csv|xlsx))"
)
TAG_KEYWORDS = {
    "odoo": ("odoo", "erp", "localization", "localización"),
    "dgii": ("dgii", "e-cf", "ecf", "ncf", "rnc", "encf"),
    "cloudflare": ("cloudflare", "tunnel", "dns"),
    "aws": ("aws", "route53", "iam"),
    "email": ("smtp", "email", "correo"),
    "auth": ("oauth", "login", "mfa", "auth"),
    "frontend": ("frontend", "react", "portal", "vite"),
    "pricing": ("pricing", "precios", "planes", "tarifas"),
    "branding": ("branding", "marca", "tagline", "naming"),
    "tutorials": ("tour", "tutorial", "joyride"),
    "demo": ("demo", "staging", "preview"),
    "chat-memory": ("chat", "historial", "prompt", "memoria"),
}
ERROR_KEYWORDS = ("error", "falta", "bloque", "pendiente", "riesgo", "deuda", "inestable", "issue", "problema")
SOLUTION_KEYWORDS = ("implement", "agreg", "corrig", "configur", "cre", "decid", "adopt", "restaur", "migr")
PENDING_KEYWORDS = ("falta", "pendiente", "siguiente paso", "next", "open", "bloque", "resta", "queda")


def build_session(source: ConversationSource, *, created_at: datetime | None = None) -> ConversationSession:
    created = created_at or datetime.now(timezone.utc)
    created_iso = created.isoformat()
    redacted_raw, redacted = redact_text(source.raw_text)
    turns = _sanitize_turns(source.turns)
    slug = slugify(source.title)
    session_id = build_session_id(source.title, redacted_raw)
    useful_prompts = _build_prompt_records(turns, session_id)
    errors = _merge_unique(item for prompt in useful_prompts for item in prompt.errors_or_gaps_detected)
    solutions = _merge_unique(item for prompt in useful_prompts for item in prompt.solution_or_decision)
    pending = _merge_unique(item for prompt in useful_prompts for item in prompt.pending_tasks)
    files = _merge_unique_raw(item for prompt in useful_prompts for item in prompt.files_or_evidence)
    tags = _merge_unique_raw(item for prompt in useful_prompts for item in prompt.tags)
    normalized_transcript = _normalize_transcript(turns)
    executive_summary = _build_executive_summary(source.title, useful_prompts, errors, solutions, pending, tags)
    sensitivity = _session_sensitivity(useful_prompts, redacted)
    return ConversationSession(
        session_id=session_id,
        title=correct_spanish_text(source.title),
        slug=slug,
        created_at=created_iso,
        source_type=source.source_type,
        source_path=source.source_path,
        raw_transcript=redacted_raw,
        normalized_transcript=normalized_transcript,
        executive_summary=executive_summary,
        useful_prompts=useful_prompts,
        errors_or_gaps_detected=errors,
        solutions_or_decisions=solutions,
        pending_tasks=pending,
        files_or_evidence=files,
        tags=tags,
        sensitivity=sensitivity,
        redaction_applied=redacted,
    )


def build_session_id(title: str, raw_transcript: str) -> str:
    digest = hashlib.sha1(f"{title}\n{raw_transcript}".encode("utf-8")).hexdigest()[:12]
    return f"{slugify(title)}-{digest}"


def slugify(value: str) -> str:
    lowered = correct_spanish_text(value).lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-") or "chat-session"


def _sanitize_turns(turns: list[ChatTurn]) -> list[ChatTurn]:
    sanitized: list[ChatTurn] = []
    for turn in turns:
        content, changed = redact_text(turn.content)
        metadata = dict(turn.metadata)
        if changed:
            metadata["redaction_applied"] = True
        sanitized.append(ChatTurn(role=turn.role, content=content, timestamp=turn.timestamp, metadata=metadata))
    return sanitized


def _build_prompt_records(turns: list[ChatTurn], session_id: str) -> list[PromptRecord]:
    prompts: list[PromptRecord] = []
    grouped = _group_user_turns(turns)
    for index, (user_turn, assistant_turns) in enumerate(grouped, start=1):
        if not _is_useful_prompt(user_turn.content):
            continue
        combined_assistant = "\n".join(turn.content for turn in assistant_turns if turn.content.strip())
        tags = detect_tags("\n".join([user_turn.content, combined_assistant]))
        normalized_prompt = to_ai_friendly_prompt(user_turn.content, tags=tags)
        outcome_summary = summarize_assistant_outcome(combined_assistant)
        errors = extract_sentences_by_keywords(combined_assistant, ERROR_KEYWORDS)
        solutions = extract_sentences_by_keywords(combined_assistant, SOLUTION_KEYWORDS)
        pending_tasks = extract_sentences_by_keywords(combined_assistant, PENDING_KEYWORDS)
        files = extract_file_references(combined_assistant)
        sensitivity = detect_sensitivity("\n".join([user_turn.content, combined_assistant]))
        status = infer_status(combined_assistant, pending_tasks)
        prompts.append(
            PromptRecord(
                prompt_id=f"{session_id}-p{index:03d}",
                source_session_id=session_id,
                index=index,
                timestamp=user_turn.timestamp,
                raw_user_prompt=user_turn.content.strip(),
                normalized_user_prompt=normalized_prompt,
                assistant_outcome_summary=outcome_summary,
                errors_or_gaps_detected=errors,
                solution_or_decision=solutions,
                status=status,
                pending_tasks=pending_tasks,
                files_or_evidence=files,
                tags=tags,
                sensitivity=sensitivity,
                redaction_applied=bool(user_turn.metadata.get("redaction_applied")),
            )
        )
    return prompts


def _group_user_turns(turns: list[ChatTurn]) -> list[tuple[ChatTurn, list[ChatTurn]]]:
    grouped: list[tuple[ChatTurn, list[ChatTurn]]] = []
    current_user: ChatTurn | None = None
    assistant_turns: list[ChatTurn] = []
    for turn in turns:
        if turn.role == "user":
            if current_user is not None:
                grouped.append((current_user, assistant_turns))
            current_user = turn
            assistant_turns = []
            continue
        if current_user is None:
            continue
        assistant_turns.append(turn)
    if current_user is not None:
        grouped.append((current_user, assistant_turns))
    return grouped


def _is_useful_prompt(text: str) -> bool:
    cleaned = correct_spanish_text(text).strip().lower()
    if cleaned in NOISE_PROMPTS:
        return False
    if len(cleaned) < 16 and cleaned.replace(".", "") in NOISE_PROMPTS:
        return False
    return len(cleaned) >= 12


def summarize_assistant_outcome(text: str) -> str:
    cleaned = correct_spanish_text(text)
    if not cleaned:
        return "Sin respuesta asociada registrada."
    sentences = split_sentences(cleaned)
    high_signal = [
        sentence
        for sentence in sentences
        if any(keyword in sentence.lower() for keyword in ("implement", "qued", "valid", "pendiente", "bloque"))
    ]
    summary_sentences = high_signal[:2] or sentences[:2]
    return " ".join(summary_sentences).strip()


def extract_sentences_by_keywords(text: str, keywords: tuple[str, ...]) -> list[str]:
    cleaned = correct_spanish_text(text)
    matches = [
        sentence
        for sentence in split_sentences(cleaned)
        if any(keyword in sentence.lower() for keyword in keywords)
    ]
    return _merge_unique(matches)


def extract_file_references(text: str) -> list[str]:
    results: list[str] = []
    for match in FILE_PATTERN.finditer(text):
        value = next(group for group in match.groups() if group)
        normalized = value.replace("\\", "/").rstrip(".,)")
        results.append(normalized)
    return _merge_unique_raw(results)


def detect_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags = [
        tag
        for tag, keywords in TAG_KEYWORDS.items()
        if any(keyword in lowered for keyword in keywords)
    ]
    return sorted(tags)


def detect_sensitivity(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("password", "contraseña", "token", "cookie", "secret", "session")):
        return "high"
    if any(word in lowered for word in ("dgii", "cert", "aws", "cloudflare", "smtp", "oauth")):
        return "medium"
    return "low"


def infer_status(text: str, pending_tasks: list[str]) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("bloqueado", "blocked", "externo")):
        return "blocked"
    if pending_tasks or any(word in lowered for word in ("falta", "pendiente", "open", "resta")):
        if any(word in lowered for word in ("implementado", "resuelto", "quedó", "pasó", "passed")):
            return "partial"
        return "open"
    if any(word in lowered for word in ("implementado", "resuelto", "listo", "ok", "passed", "validado")):
        return "resolved"
    return "informational"


def _normalize_transcript(turns: list[ChatTurn]) -> str:
    blocks: list[str] = []
    for turn in turns:
        label = turn.role.capitalize()
        normalized = correct_spanish_text(turn.content)
        blocks.append(f"{label}: {normalized}")
    return "\n\n".join(blocks)


def _build_executive_summary(
    title: str,
    prompts: list[PromptRecord],
    errors: list[str],
    solutions: list[str],
    pending: list[str],
    tags: list[str],
) -> str:
    status = "sin prompts útiles"
    if prompts:
        ordered = max(prompts, key=lambda item: STATUS_PRIORITY[item.status]).status
        status = ordered
    lines = [
        f"Conversación: {correct_spanish_text(title)}",
        f"Prompts útiles detectados: {len(prompts)}",
        f"Estado agregado: {status}",
        f"Etiquetas principales: {', '.join(tags) if tags else 'sin etiquetas'}",
    ]
    if errors:
        lines.append(f"Errores o brechas destacadas: {errors[0]}")
    if solutions:
        lines.append(f"Solución o decisión principal: {solutions[0]}")
    if pending:
        lines.append(f"Pendiente principal: {pending[0]}")
    return "\n".join(lines)


def _merge_unique(items) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = correct_spanish_text(str(item)).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def _merge_unique_raw(items) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = str(item).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def _session_sensitivity(prompts: list[PromptRecord], redacted: bool) -> str:
    if redacted or any(prompt.sensitivity == "high" for prompt in prompts):
        return "high"
    if any(prompt.sensitivity == "medium" for prompt in prompts):
        return "medium"
    return "low"
