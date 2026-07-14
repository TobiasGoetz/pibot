"""Custom errors for the bot."""

import discord


class FeatureDisabled(discord.app_commands.AppCommandError):
    """Raised when a feature is disabled for the guild."""

    def __init__(self, featureName: str) -> None:
        """Initialize with the disabled feature name."""
        self.featureName = featureName
        super().__init__("This feature is disabled on this server. ")
