from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from app.chat_memory.policy import POLICY_FILENAME, detect_repo_policy
from app.chat_memory.persist import LONG_TERM_MARKER


STATUS_COMPLIANT = "compliant"
STATUS_MISSING_ARCHIVE = "missing_session_archive"
STATUS_MISSING_MEMORY = "missing_memory_update"
STATUS_MISSING_DOCS = "missing_docs_copy"
STATUS_MISSING_CATALOG = "missing_catalog_entry"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verifica cumplimiento de memoria conversacional del repo")
    parser.add_argument("--repo-root", default=os.getcwd(), help="Raíz del repo a verificar")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = assess_chat_memory_compliance(args.repo_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == STATUS_COMPLIANT else 1


def assess_chat_memory_compliance(repo_root: str | Path | None = None) -> dict[str, Any]:
    effective_root = Path(repo_root or os.getcwd()).resolve()
    policy = detect_repo_policy(repo_root=effective_root, cwd=effective_root)
    repo_root_path = policy.repo_root if policy is not None else effective_root
    notes_dir = repo_root_path / ".ai_context" / "notes"
    policy_path = notes_dir / POLICY_FILENAME
    catalog_path = notes_dir / "prompt_catalog.json"
    memory_path = notes_dir / "LONG_TERM_PROMPT_MEMORY.md"

    issues: list[str] = []
    if not policy_path.exists():
        issues.append("missing_policy_file")

    if not catalog_path.exists():
        return _report(
            status=STATUS_MISSING_CATALOG,
            repo_root=repo_root_path,
            issues=issues + ["missing_prompt_catalog"],
            last_session=None,
        )

    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _report(
            status=STATUS_MISSING_CATALOG,
            repo_root=repo_root_path,
            issues=issues + ["invalid_prompt_catalog"],
            last_session=None,
        )

    sessions = catalog.get("sessions", [])
    prompts = catalog.get("prompts", [])
    if not sessions:
        return _report(
            status=STATUS_MISSING_CATALOG,
            repo_root=repo_root_path,
            issues=issues + ["missing_session_entries"],
            last_session=None,
        )

    sessions.sort(key=lambda item: item.get("created_at", ""))
    last_session = sessions[-1]
    last_session_id = str(last_session.get("session_id", "")).strip()
    prompt_matches = [item for item in prompts if item.get("source_session_id") == last_session_id]
    if not prompt_matches:
        return _report(
            status=STATUS_MISSING_CATALOG,
            repo_root=repo_root_path,
            issues=issues + ["missing_prompt_entries_for_last_session"],
            last_session=last_session,
        )

    session_log_path = repo_root_path / str(last_session.get("session_log_path", ""))
    compact_session_path = repo_root_path / str(last_session.get("compact_session_path", ""))
    docs_prompt_path = repo_root_path / str(last_session.get("docs_prompt_path", ""))

    archive_missing = [name for name, path in (
        ("missing_session_log", session_log_path),
        ("missing_compact_session", compact_session_path),
    ) if not path.exists()]
    if archive_missing:
        return _report(
            status=STATUS_MISSING_ARCHIVE,
            repo_root=repo_root_path,
            issues=issues + archive_missing,
            last_session=last_session,
        )

    if not docs_prompt_path.exists():
        return _report(
            status=STATUS_MISSING_DOCS,
            repo_root=repo_root_path,
            issues=issues + ["missing_docs_prompt_copy"],
            last_session=last_session,
        )

    if not memory_path.exists():
        return _report(
            status=STATUS_MISSING_MEMORY,
            repo_root=repo_root_path,
            issues=issues + ["missing_long_term_memory_file"],
            last_session=last_session,
        )

    memory_text = memory_path.read_text(encoding="utf-8")
    marker_start = f"{LONG_TERM_MARKER}:{last_session_id}:start"
    marker_end = f"{LONG_TERM_MARKER}:{last_session_id}:end"
    if marker_start not in memory_text or marker_end not in memory_text:
        return _report(
            status=STATUS_MISSING_MEMORY,
            repo_root=repo_root_path,
            issues=issues + ["missing_long_term_memory_marker"],
            last_session=last_session,
        )

    return _report(
        status=STATUS_COMPLIANT,
        repo_root=repo_root_path,
        issues=issues,
        last_session=last_session,
    )


def _report(
    *,
    status: str,
    repo_root: Path,
    issues: list[str],
    last_session: dict[str, Any] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "repo_root": str(repo_root),
        "issues": issues,
        "policy_file": str(repo_root / ".ai_context" / "notes" / POLICY_FILENAME),
    }
    if last_session is not None:
        payload["last_session"] = {
            "session_id": last_session.get("session_id"),
            "title": last_session.get("title"),
            "created_at": last_session.get("created_at"),
            "session_log_path": last_session.get("session_log_path"),
            "compact_session_path": last_session.get("compact_session_path"),
            "docs_prompt_path": last_session.get("docs_prompt_path"),
        }
    return payload
