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

    def setGeneralSetting(self, guildId: int, field: str, value: object) -> None:
        """Set a general setting."""
        config = self.get(guildId)
        updated = config.model_copy(update={"general": config.general.model_copy(update={field: value})})
        self.store.save(guildId, updated)

    def unsetGeneralSetting(self, guildId: int, field: str) -> None:
        """Reset a general setting to its model default."""
        default = getattr(GuildConfig().general, field)
        self.setGeneralSetting(guildId, field, default)

    def setFeatureSetting(self, guildId: int, settings: type[FeatureSettings], field: str, value: object) -> None:
        """Set a feature setting."""
        config = self.get(guildId)
        feature = getattr(config.features, settings.name)
        updatedFeature = feature.model_copy(update={field: value})
        updatedFeatures = config.features.model_copy(update={settings.name: updatedFeature})
        self.store.save(guildId, config.model_copy(update={"features": updatedFeatures}))

    def unsetFeatureSetting(self, guildId: int, settings: type[FeatureSettings], field: str) -> None:
        """Reset a feature setting to its model default."""
        defaultFeature = getattr(GuildConfig().features, settings.name)
        self.setFeatureSetting(guildId, settings, field, getattr(defaultFeature, field))

    async def remove(self, guild: discord.Guild) -> None:
        """Remove guild settings when the bot leaves."""
        self.store.delete(guild.id)
