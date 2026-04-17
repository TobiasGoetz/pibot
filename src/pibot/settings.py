"""Runtime settings for PiBot (env-backed enums)."""

import os
from enum import Enum


class COMMAND_SYNC_BEHAVIOR(str, Enum):
    """Env ``COMMAND_SYNC_BEHAVIOR``. Unset or invalid → ``GLOBAL``."""

    GLOBAL = "global"
    LOCAL = "local"

    @classmethod
    def from_env(cls) -> "COMMAND_SYNC_BEHAVIOR":
        raw = os.getenv("COMMAND_SYNC_BEHAVIOR", "").strip().lower()
        if raw:
            try:
                return cls(raw)
            except ValueError:
                pass
        return cls.GLOBAL


class ENABLE_DEV_TOOLS(str, Enum):
    """Env ``ENABLE_DEV_TOOLS``. Default ``FALSE``."""

    TRUE = "true"
    FALSE = "false"

    @classmethod
    def from_env(cls) -> "ENABLE_DEV_TOOLS":
        raw = os.getenv("ENABLE_DEV_TOOLS", "false").strip().lower()
        if raw in ("true", "1"):
            return cls.TRUE
        return cls.FALSE
