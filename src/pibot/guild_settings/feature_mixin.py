"""Mixin that adds feature settings slash commands to a GroupCog."""

from typing import ClassVar

import discord
from discord import app_commands

from pibot.bot import Bot
from pibot.guild_settings.feature_commands import sendSettingsReset, sendSettingsSet, sendSettingsView
from pibot.guild_settings.model import FeatureSettings


class FeatureSettingsMixin:
    """Adds ``/{feature} settings view|set|reset`` to a feature GroupCog."""

    featureConfig: ClassVar[type[FeatureSettings]]
    bot: Bot

    settings = app_commands.Group(name="settings", description="Configure this feature for this server")

    async def settingsFieldAutocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete settings fields for this feature."""
        lowered = current.lower()
        choices: list[app_commands.Choice[str]] = []
        for field, fieldInfo in self.featureConfig.model_fields.items():
            description = fieldInfo.description or field
            if lowered not in field.lower() and lowered not in description.lower():
                continue
            name = f"{field} — {description}" if description else field
            choices.append(app_commands.Choice(name=name[:100], value=field))
        return choices[:25]

    @app_commands.default_permissions(administrator=True)
    @settings.command(name="view", description="View settings for this server.")
    async def settingsView(self, interaction: discord.Interaction) -> None:
        """View feature settings."""
        await sendSettingsView(self.bot, interaction, self.featureConfig)

    @app_commands.default_permissions(administrator=True)
    @settings.command(name="set", description="Set a feature setting.")
    @app_commands.describe(setting="Setting to change", value="New value")
    @app_commands.autocomplete(setting=settingsFieldAutocomplete)
    async def settingsSet(self, interaction: discord.Interaction, setting: str, value: str) -> None:
        """Set a feature setting."""
        await sendSettingsSet(self.bot, interaction, self.featureConfig, setting, value)

    @app_commands.default_permissions(administrator=True)
    @settings.command(name="reset", description="Reset a feature setting to its default.")
    @app_commands.describe(setting="Setting to reset")
    @app_commands.autocomplete(setting=settingsFieldAutocomplete)
    async def settingsReset(self, interaction: discord.Interaction, setting: str) -> None:
        """Reset a feature setting."""
        await sendSettingsReset(self.bot, interaction, self.featureConfig, setting)
