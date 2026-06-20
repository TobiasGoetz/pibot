"""Guild settings — shared per-guild feature storage."""

import discord

from pibot.guild_settings.model import FeatureSettings
from pibot.guild_settings.store import SettingsStore, T


class GuildSettingsService:
    """Shared per-guild settings storage."""

    def __init__(self, store: SettingsStore) -> None:
        """Initialize the service."""
        self.store = store

    async def getFeature(self, guildId: int, model: type[T]) -> T:
        """Return feature settings for a guild."""
        return await self.store.findFeature(guildId, model.name, model)

    async def setFeatureField(self, guildId: int, model: type[FeatureSettings], field: str, value: object) -> None:
        """Set a feature setting."""
        config = await self.getFeature(guildId, model)
        updated = config.model_copy(update={field: value})
        await self.store.saveFeature(guildId, model.name, updated)

    async def unsetFeatureField(self, guildId: int, model: type[FeatureSettings], field: str) -> None:
        """Remove a feature setting from storage; defaults apply on next load."""
        await self.store.unsetFeatureField(guildId, model.name, field)

    async def remove(self, guild: discord.Guild) -> None:
        """Remove guild settings when the bot leaves."""
        await self.store.delete(guild.id)
