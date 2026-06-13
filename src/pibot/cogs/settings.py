"""Settings cog for shared per-guild configuration."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from pibot.bot import Bot
from pibot.guild_settings.general import GeneralConfig
from pibot.guild_settings.model import getFeatures

logger = logging.getLogger("cog.settings")


def _formatSettingValue(field: str, value: object) -> str:
    if value is None:
        return ""
    if field == "commandChannelId":
        return f"<#{value}>"
    return str(value)


async def generalSettingAutocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete general settings fields."""
    lowered = current.lower()
    choices: list[app_commands.Choice[str]] = []
    for field, fieldInfo in GeneralConfig.model_fields.items():
        description = fieldInfo.description or field
        if lowered not in field.lower() and lowered not in description.lower():
            continue
        name = f"{field} — {description}" if description else field
        choices.append(app_commands.Choice(name=name[:100], value=field))
    return choices[:25]


@app_commands.default_permissions(administrator=True)
class Settings(commands.GroupCog, group_name="settings", group_description="Configure PiBot for this server"):
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

    @app_commands.command(name="view", description="View general settings for this server.")
    async def view(self, interaction: discord.Interaction) -> None:
        """View general settings."""
        if interaction.guild is None:
            return

        config = self.bot.guildSettings.get(interaction.guild.id)
        lines = []
        for field, fieldInfo in GeneralConfig.model_fields.items():
            description = fieldInfo.description or field
            value = getattr(config, field)
            display = _formatSettingValue(field, value)
            lines.append(f"**{field}**\n{description}\n→ `{display or '(unset)'}`")
        embed = discord.Embed(
            title="General settings",
            description="\n\n".join(lines) if lines else "No settings defined.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="set", description="Set a general setting.")
    @app_commands.describe(setting="Setting to change", value="New value")
    @app_commands.autocomplete(setting=generalSettingAutocomplete)
    async def setCmd(
        self,
        interaction: discord.Interaction,
        setting: str,
        value: str,
    ) -> None:
        """Set a general setting."""
        if interaction.guild is None:
            return
        if setting not in GeneralConfig.model_fields:
            await interaction.response.send_message(f"Unknown setting `{setting}`.", ephemeral=True)
            return
        try:
            parsed = GeneralConfig.parseSetting(setting, value)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        self.bot.guildSettings.setGeneralSetting(interaction.guild.id, setting, parsed)
        logger.info("%s set general.%s for %s.", interaction.user, setting, interaction.guild.name)
        await interaction.response.send_message(f"Set **{setting}**.", ephemeral=True)

    @app_commands.command(name="reset", description="Reset a general setting to its default.")
    @app_commands.describe(setting="Setting to reset")
    @app_commands.autocomplete(setting=generalSettingAutocomplete)
    async def reset(self, interaction: discord.Interaction, setting: str) -> None:
        """Reset a general setting to its default."""
        if interaction.guild is None:
            return
        if setting not in GeneralConfig.model_fields:
            await interaction.response.send_message(f"Unknown setting `{setting}`.", ephemeral=True)
            return
        self.bot.guildSettings.unsetGeneralSetting(interaction.guild.id, setting)
        logger.info("%s reset general.%s for %s.", interaction.user, setting, interaction.guild.name)
        await interaction.response.send_message(f"Reset **{setting}** to default.", ephemeral=True)


async def setup(bot: Bot) -> None:
    """Set up the cog."""
    await bot.add_cog(Settings(bot))
