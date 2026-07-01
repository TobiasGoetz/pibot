"""MongoDB persistence for per-guild settings."""

import logging

from pymongo import AsyncMongoClient

from pibot.guild_settings.model import FeatureSettings

LOGGER = logging.getLogger("guild_settings.store")


class SettingsStore:
    """MongoDB access layer for the discord.settings collection."""

    def __init__(self, client: AsyncMongoClient) -> None:
        """Initialize collection handles."""
        self.collection = client["discord"]["settings"]

    async def findFeature[T: FeatureSettings](self, guildId: int, name: str, model: type[T]) -> T:
        """Return feature settings for a guild."""
        guildSettings = await self.collection.find_one({"_id": guildId})
        featureSettings = (guildSettings or {}).get("features", {}).get(name, {})
        return model.fromStored(featureSettings)

    async def saveFeature(self, guildId: int, name: str, config: FeatureSettings) -> None:
        """Persist feature fields and remove any stored fields no longer in the payload."""
        payload = config.sparseDump()
        featureKey = f"features.{name}"

        if not payload:
            guildSettings = await self.collection.find_one({"_id": guildId}) or {}
            if name in guildSettings.get("features", {}):
                await self.collection.update_one({"_id": guildId}, {"$unset": {featureKey: ""}})
            await self._cleanupEmptyDocument(guildId)
            LOGGER.info("Saved %s settings for guild %s.", name, guildId)
            return

        await self.collection.update_one(
            {"_id": guildId},
            {"$set": {featureKey: payload}},
            upsert=True,
        )
        await self._cleanupEmptyDocument(guildId)
        LOGGER.info("Saved %s settings for guild %s.", name, guildId)

    async def unsetFeatureField(self, guildId: int, name: str, field: str) -> None:
        """Remove one stored feature field."""
        featureKey = f"features.{name}"
        await self.collection.update_one(
            {"_id": guildId},
            {"$unset": {f"{featureKey}.{field}": ""}},
        )
        await self._cleanupFeatureSettings(guildId, name)
        await self._cleanupEmptyDocument(guildId)
        LOGGER.info("Unset %s.%s for guild %s.", name, field, guildId)

    async def _cleanupFeatureSettings(self, guildId: int, name: str) -> None:
        """Remove empty stored feature settings after field unsets."""
        guildSettings = await self.collection.find_one({"_id": guildId})
        featureSettings = (guildSettings or {}).get("features", {}).get(name)
        if featureSettings == {}:
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
