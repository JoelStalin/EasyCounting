from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from app.chat_memory.codec import encode_string_list, encode_text, load_dictionary, save_dictionary
from app.chat_memory.models import ConversationSession
from app.chat_memory.normalize import correct_spanish_text
from app.chat_memory.policy import ChatMemoryPolicy, detect_repo_policy, ensure_policy_file


LONG_TERM_MARKER = "<!-- chat-memory:auto -->"


def persist_session(
    session: ConversationSession,
    *,
    repo_root: str | Path,
    docs_root: str | Path | None = None,
    policy: ChatMemoryPolicy | None = None,
) -> dict[str, str]:
    root = Path(repo_root).resolve()
    effective_policy = policy or detect_repo_policy(repo_root=root, cwd=root)
    docs_base = effective_policy.docs_prompts_dir if effective_policy else Path(docs_root).resolve() if docs_root else root / "docs" / "prompts"
    session_logs_dir = root / ".ai_context" / "session_logs"
    notes_dir = root / ".ai_context" / "notes"
    session_logs_dir.mkdir(parents=True, exist_ok=True)
    notes_dir.mkdir(parents=True, exist_ok=True)
    docs_base.mkdir(parents=True, exist_ok=True)
    policy_path = ensure_policy_file(effective_policy) if effective_policy else None

    date_prefix = session.created_at[:10]
    filename = f"{date_prefix}_{session.slug}"
    session_log_path = session_logs_dir / f"{filename}_session.md"
    compact_session_path = session_logs_dir / f"{filename}_session.compact.json"
    docs_prompt_path = docs_base / f"{filename}.md"
    catalog_path = notes_dir / "prompt_catalog.json"
    memory_path = notes_dir / "LONG_TERM_PROMPT_MEMORY.md"
    dictionary_path = notes_dir / "prompt_dictionary.json"

    session_log_path.write_text(render_session_markdown(session), encoding="utf-8")
    docs_prompt_path.write_text(render_docs_markdown(session), encoding="utf-8")
    write_compact_session_archive(compact_session_path, dictionary_path, session)
    update_prompt_catalog(catalog_path, session, session_log_path, compact_session_path, docs_prompt_path, root)
    update_long_term_memory(memory_path, session, session_log_path, docs_prompt_path, root)
    return {
        "session_log": str(session_log_path),
        "compact_session": str(compact_session_path),
        "docs_prompt": str(docs_prompt_path),
        "prompt_catalog": str(catalog_path),
        "memory_file": str(memory_path),
        "prompt_dictionary": str(dictionary_path),
        "policy_file": str(policy_path) if policy_path else "",
    }


def render_session_markdown(session: ConversationSession) -> str:
    prompt_blocks = "\n\n".join(_render_prompt_block(prompt) for prompt in session.useful_prompts)
    return (
        f"# Chat Session - {session.title}\n\n"
        f"- Session ID: `{session.session_id}`\n"
        f"- Created at: `{session.created_at}`\n"
        f"- Source type: `{session.source_type}`\n"
        f"- Source path: `{session.source_path or 'n/a'}`\n"
        f"- Sensitivity: `{session.sensitivity}`\n"
        f"- Redaction applied: `{str(session.redaction_applied).lower()}`\n\n"
        f"## Executive Summary\n\n{session.executive_summary}\n\n"
        f"## Errors or Gaps\n\n{_render_list(session.errors_or_gaps_detected)}\n\n"
        f"## Solutions or Decisions\n\n{_render_list(session.solutions_or_decisions)}\n\n"
        f"## Pending Tasks\n\n{_render_list(session.pending_tasks)}\n\n"
        f"## Files or Evidence\n\n{_render_list(session.files_or_evidence)}\n\n"
        f"## Useful Prompts\n\n{prompt_blocks or 'No useful prompts detected.'}\n\n"
        f"## Raw Transcript (Sanitized)\n\n```text\n{session.raw_transcript}\n```\n\n"
        f"## Normalized Transcript\n\n```text\n{session.normalized_transcript}\n```\n"
    )


def render_docs_markdown(session: ConversationSession) -> str:
    prompt_blocks = "\n\n".join(_render_docs_prompt_block(prompt) for prompt in session.useful_prompts)
    return (
        f"# Conversación normalizada - {session.title}\n\n"
        f"- Sesión: `{session.session_id}`\n"
        f"- Fecha: `{session.created_at}`\n"
        f"- Fuente: `{session.source_type}`\n\n"
        f"## Resumen ejecutivo\n\n{session.executive_summary}\n\n"
        f"## Prompts útiles\n\n{prompt_blocks or 'No se detectaron prompts útiles.'}\n\n"
        f"## Pendientes abiertos\n\n{_render_list(session.pending_tasks)}\n\n"
        f"## Evidencia asociada\n\n{_render_list(session.files_or_evidence)}\n"
    )


def update_prompt_catalog(
    catalog_path: Path,
    session: ConversationSession,
    session_log_path: Path,
    compact_session_path: Path,
    docs_prompt_path: Path,
    repo_root: Path,
) -> None:
    if catalog_path.exists():
        try:
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            catalog = {}
    else:
        catalog = {}

    sessions = [item for item in catalog.get("sessions", []) if item.get("session_id") != session.session_id]
    prompts = [item for item in catalog.get("prompts", []) if item.get("source_session_id") != session.session_id]

    session_entry = session.to_session_index()
    session_entry["session_log_path"] = _relative_path(session_log_path, repo_root)
    session_entry["compact_session_path"] = _relative_path(compact_session_path, repo_root)
    session_entry["docs_prompt_path"] = _relative_path(docs_prompt_path, repo_root)
    sessions.append(session_entry)
    prompts.extend(
        {
            "prompt_id": prompt.prompt_id,
            "source_session_id": prompt.source_session_id,
            "index": prompt.index,
            "timestamp": prompt.timestamp,
            "status": prompt.status,
            "tags": prompt.tags,
            "sensitivity": prompt.sensitivity,
            "redaction_applied": prompt.redaction_applied,
            "archive_path": _relative_path(compact_session_path, repo_root),
            "archive_prompt_index": prompt.index - 1,
        }
        for prompt in session.useful_prompts
    )
    sessions.sort(key=lambda item: item.get("created_at", ""))
    prompts.sort(key=lambda item: (item.get("source_session_id", ""), item.get("index", 0)))

    updated = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sessions": sessions,
        "prompts": prompts,
    }
    catalog_path.write_text(json.dumps(updated, indent=2, ensure_ascii=False), encoding="utf-8")


def write_compact_session_archive(compact_path: Path, dictionary_path: Path, session: ConversationSession) -> None:
    tokens, index = load_dictionary(dictionary_path)
    compact_payload = {
        "version": 1,
        "session_id": session.session_id,
        "title": session.title,
        "slug": session.slug,
        "created_at": session.created_at,
        "source_type": session.source_type,
        "source_path": session.source_path,
        "sensitivity": session.sensitivity,
        "redaction_applied": session.redaction_applied,
        "encoded_fields": {
            "raw_transcript": encode_text(session.raw_transcript, tokens=tokens, index=index),
            "normalized_transcript": encode_text(session.normalized_transcript, tokens=tokens, index=index),
            "executive_summary": encode_text(session.executive_summary, tokens=tokens, index=index),
        },
        "errors_or_gaps_detected": encode_string_list(session.errors_or_gaps_detected, tokens=tokens, index=index),
        "solutions_or_decisions": encode_string_list(session.solutions_or_decisions, tokens=tokens, index=index),
        "pending_tasks": encode_string_list(session.pending_tasks, tokens=tokens, index=index),
        "files_or_evidence": session.files_or_evidence,
        "tags": session.tags,
        "prompts": [
            {
                "prompt_id": prompt.prompt_id,
                "index": prompt.index,
                "timestamp": prompt.timestamp,
                "status": prompt.status,
                "sensitivity": prompt.sensitivity,
                "redaction_applied": prompt.redaction_applied,
                "tags": prompt.tags,
                "raw_user_prompt": encode_text(prompt.raw_user_prompt, tokens=tokens, index=index),
                "normalized_user_prompt": encode_text(prompt.normalized_user_prompt, tokens=tokens, index=index),
                "assistant_outcome_summary": encode_text(prompt.assistant_outcome_summary, tokens=tokens, index=index),
                "errors_or_gaps_detected": encode_string_list(prompt.errors_or_gaps_detected, tokens=tokens, index=index),
                "solution_or_decision": encode_string_list(prompt.solution_or_decision, tokens=tokens, index=index),
                "pending_tasks": encode_string_list(prompt.pending_tasks, tokens=tokens, index=index),
                "files_or_evidence": prompt.files_or_evidence,
            }
            for prompt in session.useful_prompts
        ],
    }
    compact_path.write_text(json.dumps(compact_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    save_dictionary(dictionary_path, tokens)


def update_long_term_memory(
    memory_path: Path,
    session: ConversationSession,
    session_log_path: Path,
    docs_prompt_path: Path,
    repo_root: Path,
) -> None:
    if memory_path.exists():
        content = memory_path.read_text(encoding="utf-8")
    else:
        content = "# Long-Term Prompt Memory\n\n## Memoria consolidada de prompts\n\n"

    marker = f"{LONG_TERM_MARKER}:{session.session_id}"
    section = (
        f"{marker}:start\n"
        f"### {session.created_at[:10]} - {session.title}\n\n"
        f"- Prompt útil consolidado desde sesión `{session.session_id}`.\n"
        f"- Resumen ejecutivo:\n"
        f"  - {session.executive_summary.replace(chr(10), chr(10) + '  - ')}\n"
        f"- Errores o brechas detectadas:\n"
        f"{_render_bullets(session.errors_or_gaps_detected)}\n"
        f"- Soluciones o decisiones:\n"
        f"{_render_bullets(session.solutions_or_decisions)}\n"
        f"- Pendientes abiertos:\n"
        f"{_render_bullets(session.pending_tasks)}\n"
        f"- Evidencia:\n"
        f"  - `{_relative_path(session_log_path, repo_root)}`\n"
        f"  - `{_relative_path(docs_prompt_path, repo_root)}`\n"
        f"{marker}:end"
    )

    if f"{marker}:start" in content and f"{marker}:end" in content:
        start = content.index(f"{marker}:start")
        end = content.index(f"{marker}:end") + len(f"{marker}:end")
        content = f"{content[:start]}{section}{content[end:]}"
    else:
        anchor = "## Errores recurrentes detectados en prompts del usuario"
        if anchor in content:
            content = content.replace(anchor, f"{section}\n\n{anchor}", 1)
        else:
            if not content.endswith("\n"):
                content += "\n"
            content += f"\n{section}\n"
    memory_path.write_text(content, encoding="utf-8")


def _render_prompt_block(prompt: object) -> str:
    from app.chat_memory.models import PromptRecord

    assert isinstance(prompt, PromptRecord)
    return (
        f"### Prompt {prompt.index}\n\n"
        f"- Prompt ID: `{prompt.prompt_id}`\n"
        f"- Status: `{prompt.status}`\n"
        f"- Sensitivity: `{prompt.sensitivity}`\n"
        f"- Tags: `{', '.join(prompt.tags) if prompt.tags else 'sin etiquetas'}`\n\n"
        f"**Raw user prompt**\n\n```text\n{prompt.raw_user_prompt}\n```\n\n"
        f"**Normalized user prompt**\n\n```text\n{prompt.normalized_user_prompt}\n```\n\n"
        f"**Assistant outcome summary**\n\n{prompt.assistant_outcome_summary}\n\n"
        f"**Errors or gaps**\n\n{_render_list(prompt.errors_or_gaps_detected)}\n\n"
        f"**Solution or decision**\n\n{_render_list(prompt.solution_or_decision)}\n\n"
        f"**Pending tasks**\n\n{_render_list(prompt.pending_tasks)}\n\n"
        f"**Files or evidence**\n\n{_render_list(prompt.files_or_evidence)}\n"
    )


def _render_docs_prompt_block(prompt: object) -> str:
    from app.chat_memory.models import PromptRecord

    assert isinstance(prompt, PromptRecord)
    return (
        f"### Prompt {prompt.index}\n\n"
        f"**Normalizado**\n\n```text\n{prompt.normalized_user_prompt}\n```\n\n"
        f"**Resultado**\n\n{prompt.assistant_outcome_summary}\n\n"
        f"**Pendientes**\n\n{_render_list(prompt.pending_tasks)}"
    )


def _render_list(items: list[str]) -> str:
    if not items:
        return "- Ninguno."
    return "\n".join(f"- {correct_spanish_text(item)}" for item in items)


def _render_bullets(items: list[str]) -> str:
    if not items:
        return "  - Ninguno."
    return "\n".join(f"  - {correct_spanish_text(item)}" for item in items)


def _relative_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()
