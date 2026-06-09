"""Guild settings — shared storage, general settings, and feature toggles."""

import logging
import time
from typing import Any, Protocol

from pibot.guild_settings.feature import getFeature, getFeatures
from pibot.guild_settings.general import GeneralConfig, resolve as resolveGeneral
from pibot.guild_settings.store import SettingsStore
from pibot.guild_settings.util import getNested

LOGGER = logging.getLogger("guild_settings.service")
CACHE_TTL_SECONDS = 60


class GuildLike(Protocol):
    """Minimal guild interface for settings initialization."""

    id: int
    name: str


class GuildSettingsService:
    """Shared per-guild settings storage and general configuration."""

    def __init__(self, store: SettingsStore) -> None:
        """Initialize the service."""
        self.store = store
        self._cache: dict[int, tuple[dict, float]] = {}
        getFeatures()

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

    async def ensure(self, guild: GuildLike) -> None:
        """Ensure a guild document exists (overrides only; defaults live in code)."""
        self.store.ensureGuild(guild.id, guild.name)
        self.invalidateCache(guild.id)

    async def remove(self, guild: GuildLike) -> None:
        """Remove guild settings when the bot leaves."""
        self.store.delete(guild.id)
        self.invalidateCache(guild.id)

    async def isFeatureEnabled(self, guildId: int, feature: str) -> bool:
        """Return whether a feature is enabled for the guild."""
        featureConfig = getFeature(feature)
        if featureConfig is None:
            return False
        document = self.getDocument(guildId)
        enabled = getNested(document, ("features", feature, "enabled"))
        if enabled is not None:
            return bool(enabled)
        return featureConfig.defaultEnabled

    async def setFeatureEnabled(self, guildId: int, feature: str, enabled: bool) -> None:
        """Enable or disable a feature for the guild."""
        featureConfig = getFeature(feature)
        if featureConfig is None:
            raise ValueError(f"Unknown feature: {feature}")
        path = f"features.{feature}.enabled"
        if enabled == featureConfig.defaultEnabled:
            self.unsetPath(guildId, path)
        else:
            self.setPath(guildId, path, enabled)

    async def isFeatureAvailable(self, guildId: int, feature: str) -> bool:
        """Return whether a feature is enabled and has required credentials."""
        featureConfig = getFeature(feature)
        if featureConfig is None:
            return False
        enabled = await self.isFeatureEnabled(guildId, feature)
        return featureConfig.isAvailable(self.getDocument(guildId), enabled=enabled)

    async def resolveFeature(self, guildId: int, feature: str) -> Any:
        """Return resolved settings for a feature."""
        featureConfig = getFeature(feature)
        if featureConfig is None:
            raise ValueError(f"Unknown feature: {feature}")
        enabled = await self.isFeatureEnabled(guildId, feature)
        return featureConfig.resolve(self.getDocument(guildId), enabled=enabled)

    async def general(self, guildId: int) -> GeneralConfig:
        """Return resolved general settings."""
        return resolveGeneral(self.getDocument(guildId))

    async def getPrefix(self, guildId: int) -> str:
        """Return the command prefix for a guild."""
        return (await self.general(guildId)).prefix

    async def getCommandChannelId(self, guildId: int) -> int | None:
        """Return the restricted command channel ID, if any."""
        return (await self.general(guildId)).commandChannelId

    async def setPrefix(self, guildId: int, prefix: str) -> None:
        """Set the command prefix for a guild."""
        self.setPath(guildId, "general.prefix", prefix)

    async def resetPrefix(self, guildId: int) -> None:
        """Reset the command prefix to the default."""
        self.unsetPath(guildId, "general.prefix")

    async def setCommandChannelId(self, guildId: int, channelId: int) -> None:
        """Restrict text commands to a channel."""
        self.setPath(guildId, "general.commandChannelId", channelId)

    async def resetCommandChannelId(self, guildId: int) -> None:
        """Allow text commands in any channel."""
        self.unsetPath(guildId, "general.commandChannelId")
