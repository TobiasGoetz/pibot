"""Settings cog for shared per-guild configuration."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from pibot.bot import Bot
from pibot.guild_settings.model import getFeature, getFeatures, getSettings, readPath, resolveSettingKey

logger = logging.getLogger("cog.settings")


def _autocompleteChoices(values: list[str], current: str) -> list[app_commands.Choice[str]]:
    lowered = current.lower()
    return [app_commands.Choice(name=value, value=value) for value in values if lowered in value.lower()][:25]


async def featureNameAutocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete registered feature names."""
    return _autocompleteChoices(list(getFeatures()), current)


async def settingKeyAutocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete registered setting keys."""
    keys = [
        f"{settingsClass.name}.{path}"
        for settingsClass in getFeatures().values()
        for path, _ in getSettings(settingsClass)
    ]
    return _autocompleteChoices(keys, current)


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
            resolved = await self.bot.guildSettings.resolve(interaction.guild.id, settingsClass)
            enabled = resolved.enabled
            available = await self.bot.guildSettings.isFeatureAvailable(interaction.guild.id, name)
            status = "on" if enabled else "off"
            if enabled and not available:
                status += " (not configured)"
            lines.append(f"**{name}** — {status}\n{settingsClass.description}")
        embed = discord.Embed(title="Features", description="\n\n".join(lines))
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="view", description="View settings for this server.")
    @app_commands.describe(feature="Feature to view (omit for general settings)")
    @app_commands.autocomplete(feature=featureNameAutocomplete)
    async def view(self, interaction: discord.Interaction, feature: str | None = None) -> None:
        """View general or feature settings."""
        if interaction.guild is None:
            return
        if feature is None:
            general = await self.bot.guildSettings.general(interaction.guild.id)
            channel = f"<#{general.commandChannelId}>" if general.commandChannelId else "(any channel)"
            embed = discord.Embed(
                title="General settings",
                description=f"**prefix** — `{general.prefix}`\n**command channel** — {channel}",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        settingsClass = getFeature(feature)
        if settingsClass is None:
            await interaction.response.send_message(f"Unknown feature `{feature}`.", ephemeral=True)
            return

        resolved = await self.bot.guildSettings.resolve(interaction.guild.id, settingsClass)
        lines = []
        for path, description in getSettings(settingsClass):
            value = readPath(resolved, path)
            display = "" if value is None else str(value)
            lines.append(f"**{settingsClass.name}.{path}**\n{description}\n→ `{display}`")
        embed = discord.Embed(
            title=f"Settings — {feature}",
            description="\n\n".join(lines) if lines else "No settings defined.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="set", description="Set a feature setting.")
    @app_commands.describe(key="Setting key (feature.setting)", value="New value")
    @app_commands.autocomplete(key=settingKeyAutocomplete)
    async def setCmd(self, interaction: discord.Interaction, key: str, value: str) -> None:
        """Set a feature setting by key."""
        if interaction.guild is None:
            return
        resolved = resolveSettingKey(key)
        if resolved is None:
            await interaction.response.send_message(f"Unknown setting `{key}`.", ephemeral=True)
            return
        settingsClass, path = resolved
        try:
            parsed = settingsClass.parseSetting(path, value)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        self.bot.guildSettings.setFeatureSetting(interaction.guild.id, settingsClass, path, parsed)
        logger.info("%s set %s for %s.", interaction.user, key, interaction.guild.name)
        await interaction.response.send_message(f"Set **{key}**.", ephemeral=True)

    @app_commands.command(name="reset", description="Reset a feature setting to its default.")
    @app_commands.describe(key="Setting key (feature.setting)")
    @app_commands.autocomplete(key=settingKeyAutocomplete)
    async def reset(self, interaction: discord.Interaction, key: str) -> None:
        """Reset a feature setting override."""
        if interaction.guild is None:
            return
        resolved = resolveSettingKey(key)
        if resolved is None:
            await interaction.response.send_message(f"Unknown setting `{key}`.", ephemeral=True)
            return
        settingsClass, path = resolved
        self.bot.guildSettings.unsetFeatureSetting(interaction.guild.id, settingsClass, path)
        logger.info("%s reset %s for %s.", interaction.user, key, interaction.guild.name)
        await interaction.response.send_message(f"Reset **{key}** to default.", ephemeral=True)

    @app_commands.command(name="prefix", description="Set the prefix for text commands.")
    async def prefix(self, interaction: discord.Interaction, prefix: str) -> None:
        """Set the command prefix."""
        if interaction.guild is None:
            return
        self.bot.guildSettings.setPath(interaction.guild.id, "general.prefix", prefix)
        logger.info("%s set prefix to %s for %s.", interaction.user, prefix, interaction.guild.name)
        await interaction.response.send_message(f"Prefix set to `{prefix}`.", ephemeral=True)

    @app_commands.command(name="command_channel", description="Restrict text commands to a channel.")
    async def commandChannel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        """Set the command channel."""
        if interaction.guild is None:
            return
        self.bot.guildSettings.setPath(interaction.guild.id, "general.commandChannelId", channel.id)
        logger.info("%s set command channel to %s for %s.", interaction.user, channel.name, interaction.guild.name)
        await interaction.response.send_message(f"Command channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="reset_command_channel", description="Allow text commands in any channel.")
    async def resetCommandChannel(self, interaction: discord.Interaction) -> None:
        """Clear the command channel restriction."""
        if interaction.guild is None:
            return
        self.bot.guildSettings.unsetPath(interaction.guild.id, "general.commandChannelId")
        await interaction.response.send_message("Text commands are allowed in any channel.", ephemeral=True)


async def setup(bot: Bot) -> None:
    """Set up the cog."""
    await bot.add_cog(Settings(bot))
