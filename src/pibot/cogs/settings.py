"""Settings cog for shared per-guild configuration."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from pibot.bot import Bot
from pibot.guild_settings.feature import getFeature, getFeatures
from pibot.guild_settings.setting import getAllSettings, getSettingByKey

logger = logging.getLogger("cog.settings")


async def featureNameAutocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete registered feature names."""
    lowered = current.lower()
    choices = [app_commands.Choice(name=name, value=name) for name in getFeatures() if lowered in name.lower()]
    return choices[:25]


async def settingKeyAutocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete registered setting keys."""
    lowered = current.lower()
    choices = [
        app_commands.Choice(name=fullKey, value=fullKey) for fullKey in getAllSettings() if lowered in fullKey.lower()
    ]
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
        await self.bot.guildSettings.ensure(interaction.guild)
        lines = []
        for name, featureConfig in getFeatures().items():
            enabled = await self.bot.guildSettings.isFeatureEnabled(interaction.guild.id, name)
            available = await self.bot.guildSettings.isFeatureAvailable(interaction.guild.id, name)
            status = "on" if enabled else "off"
            if enabled and not available:
                status += " (not configured)"
            lines.append(f"**{name}** — {status}\n{featureConfig.description}")
        embed = discord.Embed(title="Features", description="\n\n".join(lines))
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="feature", description="Enable or disable a feature for this server.")
    @app_commands.describe(feature="Feature name", enabled="Whether the feature is enabled")
    @app_commands.autocomplete(feature=featureNameAutocomplete)
    async def feature(self, interaction: discord.Interaction, feature: str, enabled: bool) -> None:
        """Toggle a feature on or off."""
        if interaction.guild is None:
            return
        if feature not in getFeatures():
            await interaction.response.send_message(f"Unknown feature `{feature}`.", ephemeral=True)
            return
        await self.bot.guildSettings.ensure(interaction.guild)
        await self.bot.guildSettings.setFeatureEnabled(interaction.guild.id, feature, enabled)
        state = "enabled" if enabled else "disabled"
        logger.info("%s %s feature %s for %s.", interaction.user, state, feature, interaction.guild.name)
        await interaction.response.send_message(f"Feature **{feature}** is now **{state}**.", ephemeral=True)

    @app_commands.command(name="view", description="View settings for this server.")
    @app_commands.describe(feature="Feature to view (omit for general settings)")
    @app_commands.autocomplete(feature=featureNameAutocomplete)
    async def view(self, interaction: discord.Interaction, feature: str | None = None) -> None:
        """View general or feature settings."""
        if interaction.guild is None:
            return
        await self.bot.guildSettings.ensure(interaction.guild)

        if feature is None:
            general = await self.bot.guildSettings.general(interaction.guild.id)
            channel = f"<#{general.commandChannelId}>" if general.commandChannelId else "(any channel)"
            embed = discord.Embed(
                title="General settings",
                description=f"**prefix** — `{general.prefix}`\n**command channel** — {channel}",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        featureConfig = getFeature(feature)
        if featureConfig is None:
            await interaction.response.send_message(f"Unknown feature `{feature}`.", ephemeral=True)
            return

        resolved = await self.bot.guildSettings.resolveFeature(interaction.guild.id, feature)
        lines = [
            f"**{setting.fullKey(feature)}**\n{setting.description}\n→ `{setting.formatResolved(resolved)}`"
            for setting in featureConfig.getSettings()
        ]
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
        entry = getSettingByKey(key)
        if entry is None:
            await interaction.response.send_message(f"Unknown setting `{key}`.", ephemeral=True)
            return
        featureName, settingCls = entry
        await self.bot.guildSettings.ensure(interaction.guild)
        try:
            parsed = settingCls.parse(value)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        self.bot.guildSettings.setPath(interaction.guild.id, settingCls.mongoPath(featureName), parsed)
        logger.info("%s set %s for %s.", interaction.user, key, interaction.guild.name)
        await interaction.response.send_message(f"Set **{key}**.", ephemeral=True)

    @app_commands.command(name="reset", description="Reset a feature setting to its default.")
    @app_commands.describe(key="Setting key (feature.setting)")
    @app_commands.autocomplete(key=settingKeyAutocomplete)
    async def reset(self, interaction: discord.Interaction, key: str) -> None:
        """Reset a feature setting override."""
        if interaction.guild is None:
            return
        entry = getSettingByKey(key)
        if entry is None:
            await interaction.response.send_message(f"Unknown setting `{key}`.", ephemeral=True)
            return
        featureName, settingCls = entry
        await self.bot.guildSettings.ensure(interaction.guild)
        self.bot.guildSettings.unsetPath(interaction.guild.id, settingCls.mongoPath(featureName))
        logger.info("%s reset %s for %s.", interaction.user, key, interaction.guild.name)
        await interaction.response.send_message(f"Reset **{key}** to default.", ephemeral=True)

    @app_commands.command(name="prefix", description="Set the prefix for text commands.")
    async def prefix(self, interaction: discord.Interaction, prefix: str) -> None:
        """Set the command prefix."""
        if interaction.guild is None:
            return
        await self.bot.guildSettings.ensure(interaction.guild)
        await self.bot.guildSettings.setPrefix(interaction.guild.id, prefix)
        logger.info("%s set prefix to %s for %s.", interaction.user, prefix, interaction.guild.name)
        await interaction.response.send_message(f"Prefix set to `{prefix}`.", ephemeral=True)

    @app_commands.command(name="command_channel", description="Restrict text commands to a channel.")
    async def commandChannel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        """Set the command channel."""
        if interaction.guild is None:
            return
        await self.bot.guildSettings.ensure(interaction.guild)
        await self.bot.guildSettings.setCommandChannelId(interaction.guild.id, channel.id)
        logger.info("%s set command channel to %s for %s.", interaction.user, channel.name, interaction.guild.name)
        await interaction.response.send_message(f"Command channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="reset_command_channel", description="Allow text commands in any channel.")
    async def resetCommandChannel(self, interaction: discord.Interaction) -> None:
        """Clear the command channel restriction."""
        if interaction.guild is None:
            return
        await self.bot.guildSettings.ensure(interaction.guild)
        await self.bot.guildSettings.resetCommandChannelId(interaction.guild.id)
        await interaction.response.send_message("Text commands are allowed in any channel.", ephemeral=True)


async def setup(bot: Bot) -> None:
    """Set up the cog."""
    await bot.add_cog(Settings(bot))
