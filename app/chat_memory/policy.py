from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path


DEFAULT_REPO_ROOT = Path(r"C:\Users\yoeli\Documents\dgii_encf")
POLICY_ENV_REPO_ROOT = "CHAT_MEMORY_POLICY_REPO_ROOT"
POLICY_FILENAME = "chat_memory_policy.json"


@dataclass(slots=True)
class ChatMemoryPolicy:
    repo_root: Path
    canonical_repo_root: Path
    close_required: bool
    redact_secrets_required: bool
    raw_transcript_required: bool
    normalized_transcript_required: bool
    update_long_term_memory_required: bool
    update_prompt_catalog_required: bool
    update_prompt_dictionary_required: bool
    session_logs_dir: Path
    notes_dir: Path
    docs_prompts_dir: Path
    policy_path: Path

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        return {
            key: str(value) if isinstance(value, Path) else value
            for key, value in payload.items()
        }


def configured_repo_root() -> Path:
    configured = os.getenv(POLICY_ENV_REPO_ROOT)
    return Path(configured).resolve() if configured else DEFAULT_REPO_ROOT.resolve()


def detect_repo_policy(*, repo_root: str | Path | None = None, cwd: str | Path | None = None) -> ChatMemoryPolicy | None:
    canonical = configured_repo_root()
    candidate = Path(repo_root or cwd or os.getcwd()).resolve()
    if candidate != canonical and canonical not in candidate.parents:
        return None
    return build_policy(canonical)


def build_policy(repo_root: str | Path) -> ChatMemoryPolicy:
    root = Path(repo_root).resolve()
    notes_dir = root / ".ai_context" / "notes"
    return ChatMemoryPolicy(
        repo_root=root,
        canonical_repo_root=root,
        close_required=True,
        redact_secrets_required=True,
        raw_transcript_required=True,
        normalized_transcript_required=True,
        update_long_term_memory_required=True,
        update_prompt_catalog_required=True,
        update_prompt_dictionary_required=True,
        session_logs_dir=root / ".ai_context" / "session_logs",
        notes_dir=notes_dir,
        docs_prompts_dir=root / "docs" / "prompts",
        policy_path=notes_dir / POLICY_FILENAME,
    )


def ensure_policy_file(policy: ChatMemoryPolicy) -> Path:
    policy.notes_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "policy_name": "repo_chat_memory_close_required",
        "repo_root": str(policy.repo_root),
        "canonical_repo_root": str(policy.canonical_repo_root),
        "close_required": policy.close_required,
        "redact_secrets_required": policy.redact_secrets_required,
        "raw_transcript_required": policy.raw_transcript_required,
        "normalized_transcript_required": policy.normalized_transcript_required,
        "update_long_term_memory_required": policy.update_long_term_memory_required,
        "update_prompt_catalog_required": policy.update_prompt_catalog_required,
        "update_prompt_dictionary_required": policy.update_prompt_dictionary_required,
        "session_logs_dir": str(policy.session_logs_dir),
        "notes_dir": str(policy.notes_dir),
        "docs_prompts_dir": str(policy.docs_prompts_dir),
    }
    policy.policy_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return policy.policy_path


def resolve_effective_roots(
    *,
    repo_root: str | Path | None = None,
    docs_root: str | Path | None = None,
    cwd: str | Path | None = None,
) -> tuple[Path, Path | None, ChatMemoryPolicy | None]:
    policy = detect_repo_policy(repo_root=repo_root, cwd=cwd)
    if policy is not None:
        return policy.repo_root, policy.docs_prompts_dir, policy
    effective_root = Path(repo_root or cwd or os.getcwd()).resolve()
    effective_docs = Path(docs_root).resolve() if docs_root else None
    return effective_root, effective_docs, None
