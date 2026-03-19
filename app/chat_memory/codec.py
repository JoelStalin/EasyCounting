from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re


TOKEN_PATTERN = re.compile(r"\s+|[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ_./:@-]+|.", re.UNICODE)


def load_dictionary(path: str | Path) -> tuple[list[str], dict[str, int]]:
    file_path = Path(path)
    if not file_path.exists():
        return [], {}
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [], {}
    tokens = payload.get("tokens") or []
    if not isinstance(tokens, list):
        return [], {}
    normalized = [str(token) for token in tokens]
    return normalized, {token: index for index, token in enumerate(normalized)}


def save_dictionary(path: str | Path, tokens: list[str]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "tokens": tokens,
    }
    file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def tokenize_text(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text)


def encode_text(text: str, *, tokens: list[str], index: dict[str, int]) -> str:
    parts: list[str] = []
    for token in tokenize_text(text):
        token_index = index.get(token)
        if token_index is None:
            token_index = len(tokens)
            tokens.append(token)
            index[token] = token_index
        parts.append(_to_base36(token_index))
    return " ".join(parts)


def decode_text(encoded: str, *, tokens: list[str]) -> str:
    if not encoded.strip():
        return ""
    decoded: list[str] = []
    for item in encoded.split():
        decoded.append(tokens[_from_base36(item)])
    return "".join(decoded)


def encode_string_list(values: list[str], *, tokens: list[str], index: dict[str, int]) -> list[str]:
    return [encode_text(value, tokens=tokens, index=index) for value in values]


def decode_string_list(values: list[str], *, tokens: list[str]) -> list[str]:
    return [decode_text(value, tokens=tokens) for value in values]


def _to_base36(number: int) -> str:
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    if number == 0:
        return "0"
    value = number
    parts: list[str] = []
    while value:
        value, remainder = divmod(value, 36)
        parts.append(alphabet[remainder])
    return "".join(reversed(parts))


def _from_base36(value: str) -> int:
    return int(value, 36)
