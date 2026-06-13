"""Guild settings — shared storage, general settings, and feature toggles."""

import logging
from typing import Any

import discord

from pibot.guild_settings.config import GuildConfig
from pibot.guild_settings.model import FeatureSettings, readPath, setDictPath, toStoredValue
from pibot.guild_settings.store import SettingsStore

LOGGER = logging.getLogger("guild_settings.service")


class GuildSettingsService:
    """Shared per-guild settings storage and general configuration."""

    def __init__(self, store: SettingsStore) -> None:
        """Initialize the service."""
        self.store = store

    def get(self, guildId: int) -> GuildConfig:
        """Return settings for a guild."""
        stored = self.store.findById(guildId)
        return stored if stored is not None else GuildConfig()

    def save(self, guildId: int, config: GuildConfig) -> None:
        """Persist settings."""
        self.store.save(guildId, config)

    def _updateAtPath(self, guildId: int, path: str, value: Any) -> GuildConfig:
        data = self.get(guildId).model_dump()
        setDictPath(data, path, value)
        config = GuildConfig.model_validate(data)
        self.save(guildId, config)
        return config

    def setPath(self, guildId: int, path: str, value: Any) -> None:
        """Set a nested field."""
        self._updateAtPath(guildId, path, value)

    def unsetPath(self, guildId: int, path: str) -> None:
        """Reset a nested field to its model default."""
        defaultValue = toStoredValue(readPath(GuildConfig(), path))
        self._updateAtPath(guildId, path, defaultValue)

    def setFeatureSetting(self, guildId: int, settings: type[FeatureSettings], path: str, value: Any) -> None:
        """Set a feature setting."""
        self._updateAtPath(guildId, f"features.{settings.name}.{path}", value)

    def unsetFeatureSetting(self, guildId: int, settings: type[FeatureSettings], path: str) -> None:
        """Reset a feature setting to its model default."""
        defaultFeature = getattr(GuildConfig().features, settings.name)
        defaultValue = toStoredValue(readPath(defaultFeature, path))
        self._updateAtPath(guildId, f"features.{settings.name}.{path}", defaultValue)

    async def remove(self, guild: discord.Guild) -> None:
        """Remove guild settings when the bot leaves."""
        self.store.delete(guild.id)
