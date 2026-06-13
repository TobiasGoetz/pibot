"""Guild settings — shared storage, general settings, and feature toggles."""

import logging
import time
from typing import Any

import discord

from pibot.guild_settings.config import GuildConfig
from pibot.guild_settings.model import FeatureSettings, readPath, setDictPath, toStoredValue
from pibot.guild_settings.store import SettingsStore

LOGGER = logging.getLogger("guild_settings.service")
CACHE_TTL_SECONDS = 60


class GuildSettingsService:
    """Shared per-guild settings storage and general configuration."""

    def __init__(self, store: SettingsStore) -> None:
        """Initialize the service."""
        self.store = store
        self._cache: dict[int, tuple[GuildConfig, float]] = {}

    def invalidateCache(self, guildId: int) -> None:
        """Drop cached settings for a guild."""
        self._cache.pop(guildId, None)

    def get(self, guildId: int) -> GuildConfig:
        """Return settings for a guild."""
        cached = self._cache.get(guildId)
        now = time.monotonic()
        if cached and now - cached[1] < CACHE_TTL_SECONDS:
            return cached[0]

        stored = self.store.findById(guildId)
        config = stored if stored is not None else GuildConfig()
        self._cache[guildId] = (config, now)
        return config

    def save(self, guildId: int, config: GuildConfig) -> None:
        """Persist settings and invalidate the cache."""
        self.store.save(guildId, config)
        self.invalidateCache(guildId)

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
        self.invalidateCache(guild.id)
