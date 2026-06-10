"""Shared helpers for guild settings documents."""

from typing import Any


def getNested(document: dict, path: tuple[str, ...]) -> Any:
    """Read a nested value from a document."""
    current: Any = document
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current
