"""Settings cog."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from pibot.bot import Bot
from pibot.cogs.error_handler import handleInteractionError
from pibot.guild_settings.errors import GuildSettingsError
from pibot.guild_settings.settings_ui import sendSettingsPanel

logger = logging.getLogger("cog.settings")


class Settings(commands.Cog):
    """Guild-wide settings navigation."""

    def __init__(self, bot: Bot) -> None:
        """Initialize the cog."""
        self.bot = bot

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="settings", description="Configure bot features for this server.")
    async def settings(self, interaction: discord.Interaction) -> None:
        """Open the interactive settings panel."""
        await sendSettingsPanel(self.bot, interaction)

    @settings.error
    async def settingsError(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        """Handle expected failures while opening the settings panel."""
        original = error.original if isinstance(error, app_commands.CommandInvokeError) else error
        if isinstance(original, GuildSettingsError):
            await handleInteractionError(
                interaction,
                original,
                userErrorType=GuildSettingsError,
                fallbackMessage="Something went wrong while updating settings.",
                log=logger,
                logMessage="Unhandled error opening settings panel.",
            )
            return
        raise error
