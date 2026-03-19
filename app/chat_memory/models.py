from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ChatTurn:
    role: str
    content: str
    timestamp: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ConversationSource:
    title: str
    raw_text: str
    source_type: str
    source_path: str | None = None
    turns: list[ChatTurn] = field(default_factory=list)


@dataclass(slots=True)
class PromptRecord:
    prompt_id: str
    source_session_id: str
    index: int
    timestamp: str | None
    raw_user_prompt: str
    normalized_user_prompt: str
    assistant_outcome_summary: str
    errors_or_gaps_detected: list[str]
    solution_or_decision: list[str]
    status: str
    pending_tasks: list[str]
    files_or_evidence: list[str]
    tags: list[str]
    sensitivity: str
    redaction_applied: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ConversationSession:
    session_id: str
    title: str
    slug: str
    created_at: str
    source_type: str
    source_path: str | None
    raw_transcript: str
    normalized_transcript: str
    executive_summary: str
    useful_prompts: list[PromptRecord]
    errors_or_gaps_detected: list[str]
    solutions_or_decisions: list[str]
    pending_tasks: list[str]
    files_or_evidence: list[str]
    tags: list[str]
    sensitivity: str
    redaction_applied: bool

    def to_session_index(self) -> dict[str, Any]:
        status_counts: dict[str, int] = {}
        for prompt in self.useful_prompts:
            status_counts[prompt.status] = status_counts.get(prompt.status, 0) + 1
        return {
            "session_id": self.session_id,
            "title": self.title,
            "slug": self.slug,
            "created_at": self.created_at,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "prompt_count": len(self.useful_prompts),
            "status_counts": status_counts,
            "pending_tasks": self.pending_tasks,
            "files_or_evidence": self.files_or_evidence,
            "tags": self.tags,
            "sensitivity": self.sensitivity,
            "redaction_applied": self.redaction_applied,
        }
