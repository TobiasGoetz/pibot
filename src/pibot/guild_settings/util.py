"""Shared helpers for guild settings documents."""

from typing import Any


def maskSecret(value: str | None) -> str:
    """Mask a secret value for display."""
    if not value:
        return "(not set)"
    if len(value) <= 4:
        return "****"
    return f"****{value[-4:]}"


def getNested(document: dict, path: tuple[str, ...]) -> Any:
    """Read a nested value from a document."""
    current: Any = document
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current
