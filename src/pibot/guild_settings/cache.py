"""Cache backends for guild settings."""

from typing import Protocol

from valkey.asyncio import Valkey

from pibot.guild_settings.model import SettingsGroup

CACHE_KEY_PREFIX = "pibot:settings"


def cacheKey(guildId: int, featureName: str) -> str:
    """Return the Valkey key for one guild feature settings group."""
    return f"{CACHE_KEY_PREFIX}:{guildId}:{featureName}"


class SettingsCache(Protocol):
    """Async cache for parsed guild settings groups."""

    async def get[T: SettingsGroup](self, guildId: int, model: type[T]) -> T | None:
        """Return a cached settings group, or ``None`` on miss."""

    async def set(self, guildId: int, config: SettingsGroup) -> None:
        """Store a settings group in the cache."""

    async def close(self) -> None:
        """Release cache resources."""


class ValkeySettingsCache(SettingsCache):
    """Valkey-backed settings cache for multi-replica deployments."""

    def __init__(self, client: Valkey) -> None:
        """Initialize with an async Valkey client."""
        self._client = client

    async def get[T: SettingsGroup](self, guildId: int, model: type[T]) -> T | None:
        """Return a cached settings group, or ``None`` on miss."""
        raw = await self._client.get(cacheKey(guildId, model.name))
        if raw is None:
            return None
        return model.model_validate_json(raw)

    async def set(self, guildId: int, config: SettingsGroup) -> None:
        """Store a settings group in the cache."""
        await self._client.set(cacheKey(guildId, type(config).name), config.model_dump_json())

    async def close(self) -> None:
        """Close the Valkey client."""
        await self._client.aclose()
