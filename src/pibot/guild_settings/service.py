"""Guild settings — shared storage, general settings, and feature toggles."""

import logging
import time
from typing import Any, Protocol

from pibot.guild_settings.model import FeatureSettings, getFeature, readPath, toStoredValue
from pibot.guild_settings.general import GeneralConfig, resolve as resolveGeneral
from pibot.guild_settings.store import SettingsStore

LOGGER = logging.getLogger("guild_settings.service")
CACHE_TTL_SECONDS = 60


class GuildLike(Protocol):
    """Minimal guild interface for settings removal."""

    id: int


class GuildSettingsService:
    """Shared per-guild settings storage and general configuration."""

    def __init__(self, store: SettingsStore) -> None:
        """Initialize the service."""
        self.store = store
        self._cache: dict[int, tuple[dict, float]] = {}

    def invalidateCache(self, guildId: int) -> None:
        """Drop cached settings for a guild."""
        self._cache.pop(guildId, None)

    def getDocument(self, guildId: int) -> dict:
        """Return stored settings overrides for a guild (empty dict when none)."""
        cached = self._cache.get(guildId)
        now = time.monotonic()
        if cached and now - cached[1] < CACHE_TTL_SECONDS:
            return cached[0]

        stored = self.store.findById(guildId)
        if stored is None:
            document: dict = {}
        else:
            document = {key: stored[key] for key in ("general", "features") if key in stored}

        self._cache[guildId] = (document, now)
        return document

    def setPath(self, guildId: int, dottedPath: str, value: Any) -> None:
        """Set a nested field and invalidate the cache."""
        self.store.setPath(guildId, dottedPath, value)
        self.invalidateCache(guildId)

    def unsetPath(self, guildId: int, dottedPath: str) -> None:
        """Remove a stored override and invalidate the cache."""
        self.store.unsetPath(guildId, dottedPath)
        self.invalidateCache(guildId)

    def setFeatureSetting(self, guildId: int, settings: type[FeatureSettings], path: str, value: Any) -> None:
        """Set a feature setting, unsetting when the value matches the default."""
        defaultValue = toStoredValue(readPath(settings.resolve({}), path))
        if value == defaultValue:
            self.unsetFeatureSetting(guildId, settings, path)
        else:
            self.setPath(guildId, f"features.{settings.name}.{path}", value)

    def unsetFeatureSetting(self, guildId: int, settings: type[FeatureSettings], path: str) -> None:
        """Reset a feature setting to its model default."""
        self.unsetPath(guildId, f"features.{settings.name}.{path}")

    async def remove(self, guild: GuildLike) -> None:
        """Remove guild settings when the bot leaves."""
        self.store.delete(guild.id)
        self.invalidateCache(guild.id)

    async def isFeatureAvailable(self, guildId: int, feature: str) -> bool:
        """Return whether a feature is enabled and has required credentials."""
        settingsClass = getFeature(feature)
        if settingsClass is None:
            return False
        return settingsClass.resolve(self.getDocument(guildId)).isAvailable

    async def resolve[T: FeatureSettings](self, guildId: int, settings: type[T]) -> T:
        """Return resolved settings for a feature."""
        return settings.resolve(self.getDocument(guildId))  # type: ignore[return-value]

    async def general(self, guildId: int) -> GeneralConfig:
        """Return resolved general settings."""
        return resolveGeneral(self.getDocument(guildId))
