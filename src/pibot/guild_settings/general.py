"""General per-guild settings (prefix, command channel)."""

from pydantic import Field

from pibot.guild_settings.model import SettingsGroup

DEFAULT_PREFIX = "."
GENERAL_SETTINGS = "general"


class GeneralConfig(SettingsGroup):
    """General settings for a guild."""

    prefix: str = Field(
        default=DEFAULT_PREFIX,
        description="Text command prefix",
    )
    commandChannelId: int | None = Field(
        default=None,
        description="Channel ID restricted to text commands (omit restriction when unset)",
    )
