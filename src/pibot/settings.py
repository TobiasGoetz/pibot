"""Runtime settings for PiBot."""

import os
from enum import StrEnum


class COMMAND_SYNC_BEHAVIOR(StrEnum):
    """Env ``COMMAND_SYNC_BEHAVIOR``. Unset or invalid → ``GLOBAL``."""

    GLOBAL = "global"
    LOCAL = "local"


def command_sync_behavior() -> COMMAND_SYNC_BEHAVIOR:
    """Return the slash-command sync mode from ``COMMAND_SYNC_BEHAVIOR``."""
    raw = os.getenv("COMMAND_SYNC_BEHAVIOR", "").strip().lower()
    if raw:
        try:
            return COMMAND_SYNC_BEHAVIOR(raw)
        except ValueError:
            pass
    return COMMAND_SYNC_BEHAVIOR.GLOBAL


def is_dev_tools() -> bool:
    """Whether DevTools is on per ``ENABLE_DEV_TOOLS`` (default off). ``true`` / ``1`` → ``True``."""
    raw = os.getenv("ENABLE_DEV_TOOLS", "false").strip().lower()
    return raw in ("true", "1")
