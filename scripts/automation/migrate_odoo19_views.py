from __future__ import annotations

import ast
import html
import re
import sys
from pathlib import Path


SUPPORTED_ATTRS = {"invisible", "readonly", "required"}
OPERATOR_MAP = {
    "=": "==",
    "!=": "!=",
    ">": ">",
    "<": "<",
    ">=": ">=",
    "<=": "<=",
    "in": "in",
    "not in": "not in",
}
XMLID_RE = re.compile(r"%\(([^)]+)\)d")


def preprocess_attrs(raw: str) -> str:
    unescaped = html.unescape(raw)
    return XMLID_RE.sub(lambda match: repr(f"__XMLID__:{match.group(1)}"), unescaped)


def format_value(value) -> str:
    if isinstance(value, str):
        if value.startswith("__XMLID__:"):
            return f"%({value.split(':', 1)[1]})d"
        return repr(value)
    if value is True:
        return "True"
    if value is False:
        return "False"
    if value is None:
        return "None"
    return repr(value)


def condition_to_expr(condition) -> str:
    field, operator, value = condition
    mapped_operator = OPERATOR_MAP.get(operator)
    if mapped_operator is None:
        raise ValueError(f"Unsupported operator in attrs migration: {operator!r}")
    return f"{field} {mapped_operator} {format_value(value)}"


def is_condition(token) -> bool:
    return (
        isinstance(token, (list, tuple))
        and len(token) == 3
        and isinstance(token[0], str)
        and token[0] not in {"|", "&", "!"}
    )


def parse_prefix(tokens: list, index: int = 0) -> tuple[str, int]:
    token = tokens[index]
    if token == "!":
        operand, next_index = parse_prefix(tokens, index + 1)
        return f"(not {operand})", next_index
    if token in {"|", "&"}:
        left, next_index = parse_prefix(tokens, index + 1)
        right, next_index = parse_prefix(tokens, next_index)
        glue = "or" if token == "|" else "and"
        return f"({left} {glue} {right})", next_index
    if is_condition(token):
        return condition_to_expr(token), index + 1
    raise ValueError(f"Unsupported token in attrs domain: {token!r}")


def domain_to_expr(domain) -> str:
    if domain in (None, False):
        return "False"
    if domain in (True, []):
        return "True"
    if is_condition(domain):
        return condition_to_expr(domain)
    if isinstance(domain, (list, tuple)):
        if not domain:
            return "True"
        if isinstance(domain[0], str) and domain[0] in {"|", "&", "!"}:
            expr, next_index = parse_prefix(list(domain), 0)
            if next_index != len(domain):
                remainder = [domain_to_expr(item) for item in domain[next_index:]]
                return " and ".join([expr, *remainder])
            return expr
        parts = [domain_to_expr(item) for item in domain]
        return " and ".join(f"({part})" for part in parts)
    raise ValueError(f"Unsupported attrs domain payload: {domain!r}")


def find_tag_end(text: str, start: int) -> int:
    quote: str | None = None
    i = start
    while i < len(text):
        char = text[i]
        if quote:
            if char == quote:
                quote = None
        else:
            if char in {"'", '"'}:
                quote = char
            elif char == ">":
                return i
        i += 1
    raise ValueError("Unterminated XML tag while scanning attrs")


def replace_or_insert(tag: str, key: str, expr: str) -> str:
    pattern = re.compile(rf"""\b{key}=(["'])(.*?)\1""", re.DOTALL)
    match = pattern.search(tag)
    if not match:
        closing = "/>" if tag.endswith("/>") else ">"
        return tag[: -len(closing)] + f' {key}="{expr}"' + closing
    existing = match.group(2).strip()
    combined = expr if not existing else f"({existing}) or ({expr})"
    return tag[: match.start()] + f'{key}="{combined}"' + tag[match.end() :]


def migrate_tag(tag: str) -> str:
    attrs_match = re.search(r"""\battrs=(["'])(.*?)\1""", tag, re.DOTALL)
    if not attrs_match:
        return tag
    attrs_payload = ast.literal_eval(preprocess_attrs(attrs_match.group(2)))
    replacement = tag[: attrs_match.start()] + tag[attrs_match.end() :]
    for key, domain in attrs_payload.items():
        if key not in SUPPORTED_ATTRS:
            raise ValueError(f"Unsupported attrs key: {key!r}")
        replacement = replace_or_insert(replacement, key, domain_to_expr(domain))
    return replacement


def migrate_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8-sig")
    result: list[str] = []
    cursor = 0
    changed = False

    while cursor < len(original):
        start = original.find("<", cursor)
        if start == -1:
            result.append(original[cursor:])
            break
        result.append(original[cursor:start])
        if start + 1 < len(original) and original[start + 1] in {"!", "?", "/"}:
            result.append("<")
            cursor = start + 1
            continue
        end = find_tag_end(original, start + 1)
        tag = original[start : end + 1]
        migrated = migrate_tag(tag)
        changed = changed or migrated != tag
        result.append(migrated)
        cursor = end + 1

    if changed:
        path.write_text("".join(result), encoding="utf-8")
    return changed


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python scripts/automation/migrate_odoo19_views.py <path> [<path> ...]")
        return 1

    changed_files: list[Path] = []
    for raw_target in argv[1:]:
        target = Path(raw_target)
        files = [target] if target.is_file() else list(target.rglob("*.xml"))
        for xml_file in files:
            if migrate_file(xml_file):
                changed_files.append(xml_file)

    for changed_file in changed_files:
        print(changed_file)
    print(f"changed={len(changed_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
