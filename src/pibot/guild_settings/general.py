"""General per-guild settings (prefix, command channel)."""

from pibot.guild_settings.model import SettingsGroup

DEFAULT_PREFIX = "."


class GeneralConfig(SettingsGroup):
    """General settings for a guild."""

    prefix: str = DEFAULT_PREFIX
    commandChannelId: int | None = None
