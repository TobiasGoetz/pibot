"""Mixin that gates feature commands by guild settings."""

from typing import ClassVar

import discord

from pibot.bot import Bot
from pibot.errors import FeatureDisabled
from pibot.guild_settings.model import SettingsGroup


class FeatureSettingsMixin:
    """Gates ``/{feature}`` commands when the feature is disabled for a guild."""

    settingsGroup: ClassVar[type[SettingsGroup]]
    bot: Bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Require the feature to be enabled for this guild."""
        if interaction.guild is None:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "This command can only be used in a server.",
                    ephemeral=True,
                )
            return False

        config = await self.bot.guildSettings.getSettingsGroup(interaction.guild.id, self.settingsGroup)
        if not config.enabled:
            raise FeatureDisabled(self.settingsGroup.name)
        return True
