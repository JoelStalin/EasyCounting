from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re

from app.chat_memory.models import ChatTurn, ConversationSource


ROLE_PATTERN = re.compile(
    r"^(?P<role>user|usuario|assistant|asistente|system|sistema|developer|tool|commentary|analysis|final)"
    r"\s*[:\-]\s*(?P<content>.*)$",
    re.IGNORECASE,
)
HEADING_ROLE_PATTERN = re.compile(
    r"^#{1,6}\s*(?P<role>user|usuario|assistant|asistente|system|sistema|developer|tool|commentary|analysis|final)\b",
    re.IGNORECASE,
)
TRANSCRIPT_GLOBS = (
    "*chat*.md",
    "*conversation*.md",
    "*transcript*.md",
    "*prompt*.md",
    "*session*.md",
    "*chat*.txt",
    "*conversation*.txt",
    "*transcript*.txt",
    "*chat*.json",
    "*conversation*.json",
    "*transcript*.json",
)
DISCOVERY_SKIP_PARTS = {
    ".git",
    "node_modules",
    ".venv312",
    ".venv",
    "__pycache__",
    ".ai_context",
    "docs",
    "dist",
    "artifacts",
}


@dataclass(slots=True)
class DiscoveryCandidate:
    path: Path
    mtime: float


def load_conversation_from_file(path: str | Path, *, title: str | None = None) -> ConversationSource:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8").lstrip("\ufeff")
    turns = _parse_by_suffix(file_path.suffix.lower(), text)
    return ConversationSource(
        title=title or file_path.stem.replace("_", " ").strip(),
        raw_text=text,
        source_type="file",
        source_path=str(file_path),
        turns=turns,
    )


def load_conversation_from_text(text: str, *, title: str) -> ConversationSource:
    sanitized_text = text.lstrip("\ufeff")
    turns = parse_turns(sanitized_text)
    return ConversationSource(title=title, raw_text=sanitized_text, source_type="stdin", turns=turns)


def discover_local_conversation(*, title: str | None = None, cwd: str | Path | None = None) -> ConversationSource | None:
    roots = _discovery_roots(cwd)
    best: DiscoveryCandidate | None = None
    for root in roots:
        if not root.exists():
            continue
        for pattern in TRANSCRIPT_GLOBS:
            for candidate in root.rglob(pattern):
                if _should_skip(candidate) or not candidate.is_file():
                    continue
                info = DiscoveryCandidate(path=candidate, mtime=candidate.stat().st_mtime)
                if best is None or info.mtime > best.mtime:
                    best = info
    if best is None:
        return None
    return load_conversation_from_file(best.path, title=title)


def _should_skip(candidate: Path) -> bool:
    return any(part in DISCOVERY_SKIP_PARTS for part in candidate.parts)


def _discovery_roots(cwd: str | Path | None) -> list[Path]:
    env_value = os.getenv("CHAT_HISTORY_DISCOVERY_ROOTS")
    if env_value:
        return [Path(item).expanduser() for item in env_value.split(os.pathsep) if item.strip()]
    current = Path(cwd or os.getcwd()).resolve()
    roots = [current]
    user_profile = Path(os.path.expanduser("~"))
    roots.extend([user_profile / "Downloads", user_profile / "Documents", user_profile / ".codex"])
    return roots


def _parse_by_suffix(suffix: str, text: str) -> list[ChatTurn]:
    if suffix == ".json":
        parsed = _parse_json_turns(text)
        if parsed:
            return parsed
    return parse_turns(text)


def _parse_json_turns(text: str) -> list[ChatTurn]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []

    if isinstance(payload, dict):
        for key in ("messages", "conversation", "turns", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return _coerce_turns(value)
    if isinstance(payload, list):
        return _coerce_turns(payload)
    return []


def _coerce_turns(items: list[object]) -> list[ChatTurn]:
    turns: list[ChatTurn] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or item.get("author") or item.get("speaker") or "user").lower()
        content = item.get("content") or item.get("text") or item.get("message") or ""
        if isinstance(content, list):
            content = "\n".join(str(value) for value in content if value)
        if not str(content).strip():
            continue
        turns.append(
            ChatTurn(
                role=normalize_role(role),
                content=str(content).strip(),
                timestamp=str(item.get("timestamp") or item.get("created_at") or "") or None,
            )
        )
    return turns


def parse_turns(text: str) -> list[ChatTurn]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    turns: list[ChatTurn] = []
    current_role: str | None = None
    current_lines: list[str] = []

    def _flush() -> None:
        nonlocal current_role, current_lines
        if current_role and any(line.strip() for line in current_lines):
            turns.append(ChatTurn(role=current_role, content="\n".join(current_lines).strip()))
        current_role = None
        current_lines = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line and current_role is None:
            continue
        match = ROLE_PATTERN.match(line)
        heading_match = HEADING_ROLE_PATTERN.match(line)
        if match:
            _flush()
            current_role = normalize_role(match.group("role"))
            current_lines = [match.group("content").strip()]
            continue
        if heading_match:
            _flush()
            current_role = normalize_role(heading_match.group("role"))
            current_lines = []
            continue
        if current_role is None:
            current_role = "user"
        current_lines.append(raw_line.rstrip())
    _flush()
    if not turns and text.strip():
        return [ChatTurn(role="user", content=text.strip())]
    return turns


def normalize_role(value: str) -> str:
    lowered = value.strip().lower()
    role_map = {"usuario": "user", "asistente": "assistant", "sistema": "system"}
    return role_map.get(lowered, lowered)
