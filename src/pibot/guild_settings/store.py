"""MongoDB persistence for per-guild settings."""

import logging

from pymongo import AsyncMongoClient

from pibot.guild_settings.model import SettingsGroup
from pibot.guild_settings.serializer import fromStored

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

    async def setField(self, guildId: int, name: str, field: str, value: object) -> None:
        """Persist one settings group field."""
        fieldKey = f"features.{name}.{field}"
        await self.collection.update_one(
            {"_id": guildId},
            {"$set": {fieldKey: value}},
            upsert=True,
        )
        LOGGER.info("Set %s.%s for guild %s.", name, field, guildId)

    async def unsetField(self, guildId: int, name: str, field: str) -> None:
        """Remove one stored settings group field."""
        fieldKey = f"features.{name}.{field}"
        await self.collection.update_one(
            {"_id": guildId},
            {"$unset": {fieldKey: ""}},
        )
        LOGGER.info("Unset %s.%s for guild %s.", name, field, guildId)
