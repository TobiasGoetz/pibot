"""Shared slash-command helpers for per-feature settings."""

import logging

import discord

from pibot.bot import Bot
from pibot.guild_settings.model import FeatureSettings

logger = logging.getLogger("guild_settings.feature_commands")


def formatSettingValue(field: str, value: object) -> str:
    """Format a stored setting value for display."""
    if value is None:
        return ""
    if field == "commandChannelId":
        return f"<#{value}>"
    return str(value)


async def sendSettingsView(
    bot: Bot,
    interaction: discord.Interaction,
    configClass: type[FeatureSettings],
) -> None:
    """Send an embed listing all settings for a feature."""
    if interaction.guild is None:
        return
    config = await bot.guildSettings.getFeature(interaction.guild.id, configClass)
    lines = []
    for field, fieldInfo in configClass.model_fields.items():
        description = fieldInfo.description or field
        if fieldInfo.is_required() and field not in config.model_fields_set:
            display = "(unset)"
        else:
            display = formatSettingValue(field, getattr(config, field)) or "(unset)"
        required = " (required)" if fieldInfo.is_required() else ""
        lines.append(f"**{field}**{required}\n{description}\n→ `{display}`")
    embed = discord.Embed(
        title=f"Settings — {configClass.name}",
        description="\n\n".join(lines) if lines else "No settings defined.",
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def sendSettingsSet(
    bot: Bot,
    interaction: discord.Interaction,
    configClass: type[FeatureSettings],
    setting: str,
    value: str,
) -> None:
    """Parse and persist one feature setting."""
    if interaction.guild is None:
        return
    if setting not in configClass.model_fields:
        await interaction.response.send_message(f"Unknown setting `{setting}`.", ephemeral=True)
        return
    try:
        parsed = configClass.parseSetting(setting, value)
    except ValueError as exc:
        await interaction.response.send_message(str(exc), ephemeral=True)
        return
    await bot.guildSettings.setFeatureField(interaction.guild.id, configClass, setting, parsed)
    logger.info("%s set %s.%s for %s.", interaction.user, configClass.name, setting, interaction.guild.name)
    display = formatSettingValue(setting, parsed) or "(unset)"
    await interaction.response.send_message(f"Set **{setting}** to `{display}`.", ephemeral=True)


async def sendSettingsReset(
    bot: Bot,
    interaction: discord.Interaction,
    configClass: type[FeatureSettings],
    setting: str,
) -> None:
    """Reset one feature setting to its default."""
    if interaction.guild is None:
        return
    if setting not in configClass.model_fields:
        await interaction.response.send_message(f"Unknown setting `{setting}`.", ephemeral=True)
        return
    await bot.guildSettings.unsetFeatureField(interaction.guild.id, configClass, setting)
    logger.info("%s reset %s.%s for %s.", interaction.user, configClass.name, setting, interaction.guild.name)
    await interaction.response.send_message(f"Reset **{setting}** to default.", ephemeral=True)
