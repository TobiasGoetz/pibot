"""MongoDB persistence for per-guild settings."""

import logging

from pymongo import AsyncMongoClient

from pibot.guild_settings.model import SettingsGroup
from pibot.guild_settings.serializer import fromStored, toStored

LOGGER = logging.getLogger("guild_settings.store")


class SettingsStore:
    """MongoDB access layer for the discord.settings collection."""

    def __init__(self, client: AsyncMongoClient) -> None:
        """Initialize collection handles."""
        self.collection = client["discord"]["settings"]

    async def load[T: SettingsGroup](self, guildId: int, name: str, model: type[T]) -> T:
        """Load one settings group for a guild."""
        guildSettings = await self.collection.find_one({"_id": guildId})
        groupData = (guildSettings or {}).get("features", {}).get(name, {})
        return fromStored(model, groupData)

    async def save(self, guildId: int, name: str, config: SettingsGroup) -> None:
        """Persist settings group fields and remove any stored fields no longer in the payload."""
        payload = toStored(config)
        groupKey = f"features.{name}"

        if not payload:
            guildSettings = await self.collection.find_one({"_id": guildId}) or {}
            if name in guildSettings.get("features", {}):
                await self.collection.update_one({"_id": guildId}, {"$unset": {groupKey: ""}})
            await self._cleanupEmptyDocument(guildId)
            LOGGER.info("Saved %s settings for guild %s.", name, guildId)
            return

        await self.collection.update_one(
            {"_id": guildId},
            {"$set": {groupKey: payload}},
            upsert=True,
        )
        await self._cleanupEmptyDocument(guildId)
        LOGGER.info("Saved %s settings for guild %s.", name, guildId)

    async def resetField(self, guildId: int, name: str, field: str) -> None:
        """Remove one stored settings group field."""
        groupKey = f"features.{name}"
        await self.collection.update_one(
            {"_id": guildId},
            {"$unset": {f"{groupKey}.{field}": ""}},
        )
        await self._cleanupSettingsGroup(guildId, name)
        await self._cleanupEmptyDocument(guildId)
        LOGGER.info("Reset %s.%s for guild %s.", name, field, guildId)

    async def _cleanupSettingsGroup(self, guildId: int, name: str) -> None:
        """Remove empty stored settings groups after field unsets."""
        guildSettings = await self.collection.find_one({"_id": guildId})
        groupData = (guildSettings or {}).get("features", {}).get(name)
        if groupData == {}:
            await self.collection.update_one(
                {"_id": guildId},
                {"$unset": {f"features.{name}": ""}},
            )

    async def _cleanupEmptyDocument(self, guildId: int) -> None:
        """Remove guild settings documents that no longer store anything."""
        guildSettings = await self.collection.find_one({"_id": guildId})
        if guildSettings and guildSettings.get("features") == {}:
            await self.collection.update_one({"_id": guildId}, {"$unset": {"features": ""}})
            guildSettings = await self.collection.find_one({"_id": guildId})
        if guildSettings and set(guildSettings.keys()) == {"_id"}:
            await self.collection.delete_one({"_id": guildId})
