"""Guild settings — shared storage and general configuration."""

import discord

from pibot.guild_settings.general import GeneralConfig
from pibot.guild_settings.model import FeatureSettings
from pibot.guild_settings.store import SettingsStore, T


class GuildSettingsService:
    """Shared per-guild settings storage and general configuration."""

    def __init__(self, store: SettingsStore) -> None:
        """Initialize the service."""
        self.store = store

    def get(self, guildId: int) -> GeneralConfig:
        """Return general settings for a guild."""
        return self.store.findGeneral(guildId)

    def getFeature(self, guildId: int, model: type[T]) -> T:
        """Return feature settings for a guild."""
        return self.store.findFeature(guildId, model.name, model)

    def setGeneralSetting(self, guildId: int, field: str, value: object) -> None:
        """Set a general setting."""
        config = self.get(guildId)
        updated = config.model_copy(update={field: value})
        self.store.saveGeneral(guildId, updated)

    def unsetGeneralSetting(self, guildId: int, field: str) -> None:
        """Reset a general setting to its model default."""
        default = getattr(GeneralConfig(), field)
        self.setGeneralSetting(guildId, field, default)

    def setFeatureField(self, guildId: int, model: type[FeatureSettings], field: str, value: object) -> None:
        """Set a feature setting."""
        config = self.getFeature(guildId, model)
        updated = config.model_copy(update={field: value})
        self.store.saveFeature(guildId, model.name, updated)

    def unsetFeatureField(self, guildId: int, model: type[FeatureSettings], field: str) -> None:
        """Reset a feature setting to its model default."""
        default = getattr(model(), field)
        self.setFeatureField(guildId, model, field, default)

    async def remove(self, guild: discord.Guild) -> None:
        """Remove guild settings when the bot leaves."""
        self.store.delete(guild.id)
