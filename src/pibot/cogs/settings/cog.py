"""Settings cog."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from pibot.bot import Bot
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
