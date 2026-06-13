"""Settings cog for shared per-guild configuration."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from pibot.bot import Bot
from pibot.guild_settings.general import GENERAL_SETTINGS, GeneralConfig
from pibot.guild_settings.model import SettingsGroup, getFeature, getFeatures

logger = logging.getLogger("cog.settings")


def _autocompleteChoices(values: list[str], current: str) -> list[app_commands.Choice[str]]:
    lowered = current.lower()
    return [app_commands.Choice(name=value, value=value) for value in values if lowered in value.lower()][:25]


def _settingsClass(feature: str) -> type[SettingsGroup] | None:
    if feature == GENERAL_SETTINGS:
        return GeneralConfig
    return getFeature(feature)


def _formatSettingValue(field: str, value: object) -> str:
    if value is None:
        return ""
    if field == "commandChannelId":
        return f"<#{value}>"
    return str(value)


async def featureNameAutocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete registered feature names."""
    return _autocompleteChoices([GENERAL_SETTINGS, *getFeatures()], current)


async def featureSettingAutocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete settings for the selected group."""
    groupName = interaction.namespace.group
    if not isinstance(groupName, str):
        return []
    settingsClass = _settingsClass(groupName)
    if settingsClass is None:
        return []
    lowered = current.lower()
    choices: list[app_commands.Choice[str]] = []
    for field, fieldInfo in settingsClass.model_fields.items():
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
            featureConfig = self.bot.guildSettings.get(interaction.guild.id).features.feature(name)
            if featureConfig is None:
                continue
            status = "on" if featureConfig.enabled else "off"
            if featureConfig.enabled and not featureConfig.configured:
                status += " (not configured)"
            lines.append(f"**{name}** — {status}\n{settingsClass.description}")
        embed = discord.Embed(title="Features", description="\n\n".join(lines))
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="view", description="View settings for this server.")
    @app_commands.describe(group="Settings group to view (`general` or a feature name)")
    @app_commands.autocomplete(group=featureNameAutocomplete)
    async def view(self, interaction: discord.Interaction, group: str = GENERAL_SETTINGS) -> None:
        """View general or feature settings."""
        if interaction.guild is None:
            return

        settingsClass = _settingsClass(group)
        if settingsClass is None:
            await interaction.response.send_message(f"Unknown settings group `{group}`.", ephemeral=True)
            return

        if group == GENERAL_SETTINGS:
            config = self.bot.guildSettings.get(interaction.guild.id).general
            title = "General settings"
        else:
            featureConfig = self.bot.guildSettings.get(interaction.guild.id).features.feature(group)
            if featureConfig is None:
                await interaction.response.send_message(f"Unknown feature `{group}`.", ephemeral=True)
                return
            config = featureConfig
            title = f"Settings — {group}"

        lines = []
        for field, fieldInfo in settingsClass.model_fields.items():
            description = fieldInfo.description or field
            value = getattr(config, field)
            display = _formatSettingValue(field, value)
            lines.append(f"**{field}**\n{description}\n→ `{display or '(unset)'}`")
        embed = discord.Embed(
            title=title,
            description="\n\n".join(lines) if lines else "No settings defined.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="set", description="Set a general or feature setting.")
    @app_commands.describe(
        group="Settings group (`general` or a feature name)",
        setting="Setting to change",
        value="New value",
    )
    @app_commands.autocomplete(group=featureNameAutocomplete, setting=featureSettingAutocomplete)
    async def setCmd(
        self,
        interaction: discord.Interaction,
        group: str,
        setting: str,
        value: str,
    ) -> None:
        """Set a general or feature setting."""
        if interaction.guild is None:
            return
        settingsClass = _settingsClass(group)
        if settingsClass is None or setting not in settingsClass.model_fields:
            await interaction.response.send_message(f"Unknown setting for `{group}`.", ephemeral=True)
            return
        try:
            parsed = settingsClass.parseSetting(setting, value)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        if group == GENERAL_SETTINGS:
            self.bot.guildSettings.setGeneralSetting(interaction.guild.id, setting, parsed)
        else:
            self.bot.guildSettings.setFeatureSetting(interaction.guild.id, settingsClass, setting, parsed)
        logger.info("%s set %s.%s for %s.", interaction.user, group, setting, interaction.guild.name)
        await interaction.response.send_message(f"Set **{group}** › **{setting}**.", ephemeral=True)

    @app_commands.command(name="reset", description="Reset a general or feature setting to its default.")
    @app_commands.describe(group="Settings group (`general` or a feature name)", setting="Setting to reset")
    @app_commands.autocomplete(group=featureNameAutocomplete, setting=featureSettingAutocomplete)
    async def reset(self, interaction: discord.Interaction, group: str, setting: str) -> None:
        """Reset a general or feature setting to its default."""
        if interaction.guild is None:
            return
        settingsClass = _settingsClass(group)
        if settingsClass is None or setting not in settingsClass.model_fields:
            await interaction.response.send_message(f"Unknown setting for `{group}`.", ephemeral=True)
            return
        if group == GENERAL_SETTINGS:
            self.bot.guildSettings.unsetGeneralSetting(interaction.guild.id, setting)
        else:
            self.bot.guildSettings.unsetFeatureSetting(interaction.guild.id, settingsClass, setting)
        logger.info("%s reset %s.%s for %s.", interaction.user, group, setting, interaction.guild.name)
        await interaction.response.send_message(f"Reset **{group}** › **{setting}** to default.", ephemeral=True)


async def setup(bot: Bot) -> None:
    """Set up the cog."""
    await bot.add_cog(Settings(bot))
