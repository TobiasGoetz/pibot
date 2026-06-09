"""Shared helpers for guild settings documents."""

import copy
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


def deepMerge(base: dict, overlay: dict | None) -> dict:
    """Deep-merge overlay into a copy of base."""
    result = copy.deepcopy(base)
    if not overlay:
        return result
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deepMerge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result
