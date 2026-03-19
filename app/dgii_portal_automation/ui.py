"""Generic UI helpers built around visible labels and semantic attributes."""

from __future__ import annotations

import re
from typing import Any, Iterable


def _compile_pattern(terms: Iterable[str]) -> str:
    escaped = [re.escape(term) for term in terms if term]
    return "|".join(escaped)


def visible_text(locator: Any) -> str:
    try:
        return re.sub(r"\s+", " ", locator.inner_text().strip())
    except Exception:
        return ""


def first_visible_locator(locators: list[Any]) -> Any | None:
    for locator in locators:
        try:
            if locator.count() > 0 and locator.first.is_visible():
                return locator.first
        except Exception:
            continue
    return None


def find_input(page: Any, *terms: str, prefer_password: bool = False) -> Any | None:
    regex = _compile_pattern(terms)
    candidates: list[Any] = []
    if prefer_password:
        candidates.append(page.locator("input[type='password']"))
    if regex:
        candidates.extend(
            [
                page.get_by_label(re.compile(regex, re.IGNORECASE)),
                page.get_by_placeholder(re.compile(regex, re.IGNORECASE)),
                page.locator("input, textarea, select").filter(has_text=re.compile(regex, re.IGNORECASE)),
            ]
        )
    candidates.extend(
        [
            page.locator("input[type='text']"),
            page.locator("input:not([type])"),
            page.locator("textarea"),
        ]
    )
    return first_visible_locator(candidates)


def find_clickable(page: Any, *terms: str) -> Any | None:
    regex = _compile_pattern(terms)
    candidates: list[Any] = []
    if regex:
        candidates.extend(
            [
                page.get_by_role("button", name=re.compile(regex, re.IGNORECASE)),
                page.get_by_role("link", name=re.compile(regex, re.IGNORECASE)),
                page.locator("button").filter(has_text=re.compile(regex, re.IGNORECASE)),
                page.locator("a").filter(has_text=re.compile(regex, re.IGNORECASE)),
                page.locator("input[type='submit']"),
                page.locator("[role='button']").filter(has_text=re.compile(regex, re.IGNORECASE)),
            ]
        )
    candidates.extend([page.locator("button"), page.locator("a"), page.locator("[role='button']")])
    return first_visible_locator(candidates)


def list_visible_clickables(page: Any) -> list[Any]:
    found: list[Any] = []
    for query in ["button", "a", "[role='button']", "input[type='submit']", "input[type='button']"]:
        locator = page.locator(query)
        try:
            count = min(locator.count(), 100)
        except Exception:
            continue
        for index in range(count):
            item = locator.nth(index)
            try:
                if item.is_visible():
                    found.append(item)
            except Exception:
                continue
    return found
