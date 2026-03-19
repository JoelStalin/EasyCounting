from __future__ import annotations

import json
from pathlib import Path

from app.chat_memory.codec import decode_text, load_dictionary
from app.chat_memory.classify import build_session
from app.chat_memory.cli import main
from app.chat_memory.compliance import STATUS_COMPLIANT, STATUS_MISSING_DOCS, assess_chat_memory_compliance
from app.chat_memory.ingest import discover_local_conversation, load_conversation_from_text
from app.chat_memory.persist import persist_session
from app.chat_memory.policy import POLICY_FILENAME
from app.chat_memory.redact import redact_text


SAMPLE_TRANSCRIPT = """
User: gurada todos los prompt de esta conversacion y password: secret123
Assistant: Implementé la base del servicio y quedó resuelto en `app/services/email_service.py`.

User: agrega una funcion para organizar el historial del chat y corrige la gramatica.
Assistant: Falta persistir cloudflared como servicio y queda pendiente cerrar el bridge de Odoo.
Assistant: Solución aplicada: se creó la sección `docs/guide/19-email-smtp-service.md`.

User: ok
Assistant: listo
""".strip()


def test_redact_text_hides_sensitive_values() -> None:
    sanitized, changed = redact_text("Password: supersecret token=abc user@example.com")
    assert changed is True
    assert "supersecret" not in sanitized
    assert "user@example.com" not in sanitized
    assert "<EMAIL_REDACTED>" in sanitized


def test_build_session_normalizes_and_skips_trivial_prompts() -> None:
    source = load_conversation_from_text(SAMPLE_TRANSCRIPT, title="historial chat")
    session = build_session(source)
    assert len(session.useful_prompts) == 2
    assert "Objetivo:" in session.useful_prompts[0].normalized_user_prompt
    assert "guarda todos los prompt" in session.useful_prompts[0].normalized_user_prompt.lower()
    assert session.pending_tasks
    assert "app/services/email_service.py" in session.files_or_evidence


def test_persist_session_updates_catalog_idempotently(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".ai_context" / "notes").mkdir(parents=True)
    memory_file = repo_root / ".ai_context" / "notes" / "LONG_TERM_PROMPT_MEMORY.md"
    memory_file.write_text("# Long-Term Prompt Memory\n\n## Memoria consolidada de prompts\n\n", encoding="utf-8")
    source = load_conversation_from_text(SAMPLE_TRANSCRIPT, title="historial chat")
    session = build_session(source)

    outputs_one = persist_session(session, repo_root=repo_root)
    outputs_two = persist_session(session, repo_root=repo_root)

    catalog = json.loads((repo_root / ".ai_context" / "notes" / "prompt_catalog.json").read_text(encoding="utf-8"))
    assert len(catalog["sessions"]) == 1
    assert len(catalog["prompts"]) == 2
    assert "raw_user_prompt" not in catalog["prompts"][0]
    assert "archive_path" in catalog["prompts"][0]
    assert outputs_one["session_log"] == outputs_two["session_log"]
    memory_text = memory_file.read_text(encoding="utf-8")
    assert f"<!-- chat-memory:auto -->:{session.session_id}:start" in memory_text
    assert f"<!-- chat-memory:auto -->:{session.session_id}:end" in memory_text
    assert Path(outputs_one["docs_prompt"]).exists()
    assert Path(outputs_one["compact_session"]).exists()
    assert Path(outputs_one["prompt_dictionary"]).exists()

    compact = json.loads(Path(outputs_one["compact_session"]).read_text(encoding="utf-8"))
    tokens, _index = load_dictionary(outputs_one["prompt_dictionary"])
    decoded_summary = decode_text(compact["encoded_fields"]["executive_summary"], tokens=tokens)
    assert "Conversación" in decoded_summary
    assert tokens.count(" ") == 1


def test_discover_local_conversation_uses_configured_roots(tmp_path: Path, monkeypatch) -> None:
    source_dir = tmp_path / "imports"
    source_dir.mkdir()
    transcript = source_dir / "chat_export.md"
    transcript.write_text(SAMPLE_TRANSCRIPT, encoding="utf-8")
    monkeypatch.setenv("CHAT_HISTORY_DISCOVERY_ROOTS", str(source_dir))
    discovered = discover_local_conversation(title="descubierto", cwd=tmp_path)
    assert discovered is not None
    assert discovered.source_path == str(transcript)


def test_cli_main_supports_input_file(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    transcript = tmp_path / "conversation.md"
    transcript.write_text(SAMPLE_TRANSCRIPT, encoding="utf-8")
    exit_code = main(
        [
            "--input-file",
            str(transcript),
            "--title",
            "Conversacion de prueba",
            "--repo-root",
            str(repo_root),
            "--docs-root",
            str(repo_root / "docs" / "prompts"),
            "--close-session",
        ]
    )
    assert exit_code == 0
    catalog_path = repo_root / ".ai_context" / "notes" / "prompt_catalog.json"
    assert catalog_path.exists()


def test_dictionary_roundtrip_reuses_tokens(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    source = load_conversation_from_text(SAMPLE_TRANSCRIPT, title="historial chat")
    session = build_session(source)
    outputs = persist_session(session, repo_root=repo_root)
    tokens, _index = load_dictionary(outputs["prompt_dictionary"])
    compact = json.loads(Path(outputs["compact_session"]).read_text(encoding="utf-8"))
    decoded_prompt = decode_text(compact["prompts"][0]["raw_user_prompt"], tokens=tokens)
    assert "secret123" not in decoded_prompt.lower()
    assert "<secret_redacted>" in decoded_prompt.lower()
    assert "prompt" in " ".join(tokens).lower()


def test_cli_main_enforces_repo_policy_automatically(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    transcript = tmp_path / "conversation.md"
    transcript.write_text(SAMPLE_TRANSCRIPT, encoding="utf-8")
    monkeypatch.setenv("CHAT_MEMORY_POLICY_REPO_ROOT", str(repo_root))

    exit_code = main(
        [
            "--input-file",
            str(transcript),
            "--title",
            "Cierre diario",
            "--repo-root",
            str(repo_root),
        ]
    )

    assert exit_code == 0
    policy_path = repo_root / ".ai_context" / "notes" / POLICY_FILENAME
    assert policy_path.exists()
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    assert payload["close_required"] is True
    catalog = json.loads((repo_root / ".ai_context" / "notes" / "prompt_catalog.json").read_text(encoding="utf-8"))
    assert catalog["sessions"][-1]["title"].endswith("cierre de sesión")
    report = assess_chat_memory_compliance(repo_root)
    assert report["status"] == STATUS_COMPLIANT


def test_assess_chat_memory_compliance_detects_missing_docs_copy(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    transcript = tmp_path / "conversation.md"
    transcript.write_text(SAMPLE_TRANSCRIPT, encoding="utf-8")
    monkeypatch.setenv("CHAT_MEMORY_POLICY_REPO_ROOT", str(repo_root))

    exit_code = main(
        [
            "--input-file",
            str(transcript),
            "--title",
            "Sesion de prueba",
            "--repo-root",
            str(repo_root),
        ]
    )
    assert exit_code == 0

    catalog = json.loads((repo_root / ".ai_context" / "notes" / "prompt_catalog.json").read_text(encoding="utf-8"))
    docs_prompt_path = repo_root / catalog["sessions"][-1]["docs_prompt_path"]
    docs_prompt_path.unlink()

    report = assess_chat_memory_compliance(repo_root)
    assert report["status"] == STATUS_MISSING_DOCS
    assert "missing_docs_prompt_copy" in report["issues"]
