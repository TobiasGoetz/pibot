"""General feature settings."""

from typing import Annotated

from pydantic import Field

from pibot.guild_settings.model import SettingsGroup
from pibot.guild_settings.registry import registerSettingsGroup
from pibot.guild_settings.ui.editors import ChannelEditor


@registerSettingsGroup
class GeneralConfig(SettingsGroup):
    """General settings and utility commands for a guild."""

    name = "general"
    description = "Core bot settings and utility commands"

    prefix: str = Field(
        default=".",
        description="Text command prefix",
    )
    commandChannelId: Annotated[int | None, ChannelEditor] = Field(
        default=None,
        description="Channel ID restricted to text commands (omit restriction when unset)",
    )
    countdownMaxSeconds: int = Field(
        default=86400,
        description="Maximum countdown duration in seconds",
    )
