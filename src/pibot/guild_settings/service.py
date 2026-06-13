"""Guild settings — shared storage, general settings, and feature toggles."""

import discord

from pibot.guild_settings.config import GuildConfig
from pibot.guild_settings.model import FeatureSettings
from pibot.guild_settings.store import SettingsStore


class GuildSettingsService:
    """Shared per-guild settings storage and general configuration."""

    def __init__(self, store: SettingsStore) -> None:
        """Initialize the service."""
        self.store = store

    def get(self, guildId: int) -> GuildConfig:
        """Return settings for a guild."""
        stored = self.store.findById(guildId)
        return stored if stored is not None else GuildConfig()

    def setPrefix(self, guildId: int, prefix: str) -> None:
        """Set the text command prefix."""
        self._updateGeneral(guildId, "prefix", prefix)

    def unsetPrefix(self, guildId: int) -> None:
        """Reset the text command prefix to its default."""
        self._updateGeneral(guildId, "prefix", GuildConfig().general.prefix)

    def setCommandChannel(self, guildId: int, channelId: int) -> None:
        """Restrict text commands to a channel."""
        self._updateGeneral(guildId, "commandChannelId", channelId)

    def unsetCommandChannel(self, guildId: int) -> None:
        """Allow text commands in any channel."""
        self._updateGeneral(guildId, "commandChannelId", None)

    def setFeatureSetting(self, guildId: int, settings: type[FeatureSettings], field: str, value: object) -> None:
        """Set a feature setting."""
        self._updateFeature(guildId, settings, field, value)

    def unsetFeatureSetting(self, guildId: int, settings: type[FeatureSettings], field: str) -> None:
        """Reset a feature setting to its model default."""
        defaultFeature = getattr(GuildConfig().features, settings.name)
        self._updateFeature(guildId, settings, field, getattr(defaultFeature, field))

    def _updateGeneral(self, guildId: int, field: str, value: object) -> None:
        config = self.get(guildId)
        updated = config.model_copy(update={"general": config.general.model_copy(update={field: value})})
        self.store.save(guildId, updated)

    def _updateFeature(self, guildId: int, settings: type[FeatureSettings], field: str, value: object) -> None:
        config = self.get(guildId)
        feature = getattr(config.features, settings.name)
        updatedFeature = feature.model_copy(update={field: value})
        updatedFeatures = config.features.model_copy(update={settings.name: updatedFeature})
        self.store.save(guildId, config.model_copy(update={"features": updatedFeatures}))

    async def remove(self, guild: discord.Guild) -> None:
        """Remove guild settings when the bot leaves."""
        self.store.delete(guild.id)
