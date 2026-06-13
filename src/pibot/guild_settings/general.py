"""General per-guild settings (prefix, command channel)."""

from typing import Self

from pibot.guild_settings.model import SettingsGroup

DEFAULT_PREFIX = "."


class GeneralConfig(SettingsGroup):
    """Resolved general settings."""

    prefix: str = DEFAULT_PREFIX
    commandChannelId: int | None = None

    @classmethod
    def resolve(cls, document: dict) -> Self:
        """Resolve general settings from stored overrides."""
        return cls.model_validate(document.get("general") or {})
