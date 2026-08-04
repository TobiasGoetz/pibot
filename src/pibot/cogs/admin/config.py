"""Admin feature settings."""

from pydantic import Field

from pibot.guild_settings.model import SettingsGroup
from pibot.guild_settings.registry import registerSettingsGroup


@registerSettingsGroup
class AdminConfig(SettingsGroup):
    """Admin and moderation settings for a guild."""

    name = "admin"
    description = "Moderation commands (clear, mute, unmute)"

    maxClearAmount: int = Field(
        default=100,
        description="Maximum messages that can be cleared in one command",
    )
