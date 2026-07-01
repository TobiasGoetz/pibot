"""General feature settings."""

from pydantic import Field

from pibot.guild_settings.model import FeatureSettings


class GeneralConfig(FeatureSettings):
    """General settings and utility commands for a guild."""

    name = "general"
    description = "Core bot settings and utility commands"

    prefix: str = Field(
        default=".",
        description="Text command prefix",
    )
    commandChannelId: int | None = Field(
        default=None,
        description="Channel ID restricted to text commands (omit restriction when unset)",
    )
    countdownMaxSeconds: int = Field(
        default=86400,
        description="Maximum countdown duration in seconds",
    )
