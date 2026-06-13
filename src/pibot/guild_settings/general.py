"""General per-guild settings (prefix, command channel)."""

from typing import Annotated

from pydantic import Field

from pibot.guild_settings.model import SettingsGroup

DEFAULT_PREFIX = "."
GENERAL_SETTINGS = "general"


class GeneralConfig(SettingsGroup):
    """General settings for a guild."""

    prefix: Annotated[str, Field(description="Text command prefix")] = DEFAULT_PREFIX
    commandChannelId: Annotated[
        int | None,
        Field(description="Channel ID restricted to text commands (omit restriction when unset)"),
    ] = None
