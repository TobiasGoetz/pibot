"""Settings cog for shared per-guild configuration."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from pibot.bot import Bot
from pibot.guild_settings.model import getFeatures

logger = logging.getLogger("cog.settings")


@app_commands.default_permissions(administrator=True)
class Settings(commands.GroupCog, group_name="settings", group_description="Feature overview for this server"):
    """Shared per-guild settings commands."""

    def __init__(self, bot: Bot) -> None:
        """Initialize the cog."""
        self.bot = bot

    @app_commands.command(name="features", description="List feature modules and their status for this server.")
    async def features(self, interaction: discord.Interaction) -> None:
        """List toggleable features."""
        if interaction.guild is None:
            return
        lines = []
        for name, settingsClass in getFeatures().items():
            featureConfig = self.bot.guildSettings.getFeature(interaction.guild.id, settingsClass)
            status = "on" if featureConfig.enabled else "off"
            if featureConfig.enabled and not featureConfig.configured:
                status += " (not configured)"
            lines.append(f"**{name}** — {status}\n{settingsClass.description}\nConfigure with `/{name} settings`.")
        embed = discord.Embed(title="Features", description="\n\n".join(lines))
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: Bot) -> None:
    """Set up the cog."""
    await bot.add_cog(Settings(bot))
