"""General per-guild settings (prefix, command channel)."""

from dataclasses import dataclass

from pibot.guild_settings.util import getNested

DEFAULT_PREFIX = "."


@dataclass(frozen=True)
class GeneralConfig:
    """Resolved general settings."""

    prefix: str
    commandChannelId: int | None


def resolve(document: dict) -> GeneralConfig:
    """Resolve general settings from stored overrides."""
    prefix = getNested(document, ("general", "prefix")) or DEFAULT_PREFIX
    commandChannelId = getNested(document, ("general", "commandChannelId"))
    return GeneralConfig(prefix=prefix, commandChannelId=commandChannelId)
