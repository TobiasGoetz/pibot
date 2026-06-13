"""Custom errors for the bot."""

import discord


class UserNotConnectedToVoice(discord.app_commands.AppCommandError):
    """Raised when a user is not connected to a voice channel."""


class BotNotConnectedToVoice(discord.app_commands.AppCommandError):
    """Raised when the bot is not connected to a voice channel."""


class BotNotPlayingAudio(discord.app_commands.AppCommandError):
    """Raised when the bot is not playing anything."""


class FeatureDisabled(discord.app_commands.AppCommandError):
    """Raised when a feature is disabled for the guild."""

    def __init__(self, featureName: str) -> None:
        """Initialize with the disabled feature name."""
        self.featureName = featureName
        super().__init__(
            f"This feature is disabled on this server. "
            f"An administrator can enable it with `/{featureName} settings set enabled true`."
        )


class FeatureNotConfigured(discord.app_commands.AppCommandError):
    """Raised when a feature is enabled but missing required configuration."""

    def __init__(self, featureName: str) -> None:
        """Initialize with the feature name."""
        self.featureName = featureName
        super().__init__(
            f"**{featureName}** is not configured for this server. "
            f"An administrator can review required settings with `/{featureName} settings view`."
        )
