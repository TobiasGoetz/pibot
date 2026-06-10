"""General per-guild settings (prefix, command channel)."""

from pydantic import BaseModel, ConfigDict

DEFAULT_PREFIX = "."


class GeneralConfig(BaseModel):
    """Resolved general settings."""

    model_config = ConfigDict(frozen=True)

    prefix: str = DEFAULT_PREFIX
    commandChannelId: int | None = None


def resolve(document: dict) -> GeneralConfig:
    """Resolve general settings from stored overrides."""
    stored = document.get("general") or {}
    return GeneralConfig.model_validate(stored)
