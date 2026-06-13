"""Admin feature settings."""

from pydantic import Field

from pibot.guild_settings.model import FeatureSettings

DEFAULT_MUTED_ROLE_NAME = "Muted"
DEFAULT_MAX_CLEAR_AMOUNT = 100


class AdminConfig(FeatureSettings):
    """Admin and moderation settings for a guild."""

    name = "admin"
    description = "Moderation commands (clear, mute, unmute)"

    mutedRoleName: str = Field(
        default=DEFAULT_MUTED_ROLE_NAME,
        description="Name of the role assigned when muting members",
    )
    maxClearAmount: int = Field(
        default=DEFAULT_MAX_CLEAR_AMOUNT,
        description="Maximum messages that can be cleared in one command",
    )

    @property
    def configured(self) -> bool:
        """Admin commands do not require external configuration."""
        return True
