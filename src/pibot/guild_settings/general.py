"""General per-guild settings (prefix, command channel)."""

from typing import Self

from pydantic import BaseModel, ConfigDict

DEFAULT_PREFIX = "."


class GeneralConfig(BaseModel):
    """Resolved general settings."""

    model_config = ConfigDict(frozen=True)

    prefix: str = DEFAULT_PREFIX
    commandChannelId: int | None = None

    @classmethod
    def resolve(cls, document: dict) -> Self:
        """Resolve general settings from stored overrides."""
        return cls.model_validate(document.get("general") or {})
