"""General feature settings."""

from pydantic import Field

from pibot.guild_settings.model import FeatureSettings

DEFAULT_PREFIX = "."
DEFAULT_COUNTDOWN_MAX_SECONDS = 86400


class GeneralConfig(FeatureSettings):
    """General settings and utility commands for a guild."""

    name = "general"
    description = "Core bot settings and utility commands"

    prefix: str = Field(
        default=DEFAULT_PREFIX,
        description="Text command prefix",
    )
    commandChannelId: int | None = Field(
        default=None,
        description="Channel ID restricted to text commands (omit restriction when unset)",
    )
    countdownMaxSeconds: int = Field(
        default=DEFAULT_COUNTDOWN_MAX_SECONDS,
        description="Maximum countdown duration in seconds",
    )

    @property
    def configured(self) -> bool:
        """General settings always have usable defaults."""
        return True
