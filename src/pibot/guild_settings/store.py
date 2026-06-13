"""MongoDB persistence for per-guild settings."""

import logging
from typing import Any, TypeVar

import pymongo

from pibot.guild_settings.model import FeatureSettings

LOGGER = logging.getLogger("guild_settings.store")

T = TypeVar("T", bound=FeatureSettings)


class SettingsStore:
    """MongoDB access layer for the discord.settings collection."""

    def __init__(self, client: pymongo.MongoClient) -> None:
        """Initialize collection handles."""
        self.collection = client["discord"]["settings"]

    def findFeature(self, guildId: int, name: str, model: type[T]) -> T:
        """Return feature settings for a guild."""
        raw = self.collection.find_one({"_id": guildId})
        section = (raw or {}).get("features", {}).get(name, {})
        return model.fromStored(section)

    def saveFeature(self, guildId: int, name: str, config: FeatureSettings) -> None:
        """Persist feature fields and remove any stored fields no longer in the payload."""
        payload = config.sparseDump()
        featureKey = f"features.{name}"
        raw = self.collection.find_one({"_id": guildId}) or {}
        current = raw.get("features", {}).get(name, {})

        if not payload:
            if name in raw.get("features", {}):
                self.collection.update_one({"_id": guildId}, {"$unset": {featureKey: ""}})
            self._cleanupEmptyDocument(guildId)
            LOGGER.info("Saved %s settings for guild %s.", name, guildId)
            return

        update: dict[str, dict[str, Any]] = {}
        setOps = {f"{featureKey}.{field}": value for field, value in payload.items()}
        unsetOps = {f"{featureKey}.{field}": "" for field in current if field not in payload}
        if setOps:
            update["$set"] = setOps
        if unsetOps:
            update["$unset"] = unsetOps
        if update:
            self.collection.update_one({"_id": guildId}, update, upsert=True)
        self._cleanupEmptyDocument(guildId)
        LOGGER.info("Saved %s settings for guild %s.", name, guildId)

    def unsetFeatureField(self, guildId: int, name: str, field: str) -> None:
        """Remove one stored feature field."""
        featureKey = f"features.{name}"
        self.collection.update_one(
            {"_id": guildId},
            {"$unset": {f"{featureKey}.{field}": ""}},
        )
        self._cleanupFeatureSection(guildId, name)
        self._cleanupEmptyDocument(guildId)
        LOGGER.info("Unset %s.%s for guild %s.", name, field, guildId)

    def _cleanupFeatureSection(self, guildId: int, name: str) -> None:
        """Remove an empty feature section after field unsets."""
        raw = self.collection.find_one({"_id": guildId})
        if raw and raw.get("features", {}).get(name) == {}:
            self.collection.update_one(
                {"_id": guildId},
                {"$unset": {f"features.{name}": ""}},
            )

    def _cleanupEmptyDocument(self, guildId: int) -> None:
        """Remove guild settings documents that no longer store anything."""
        raw = self.collection.find_one({"_id": guildId})
        if raw and raw.get("features") == {}:
            self.collection.update_one({"_id": guildId}, {"$unset": {"features": ""}})
            raw = self.collection.find_one({"_id": guildId})
        if raw and set(raw.keys()) == {"_id"}:
            self.collection.delete_one({"_id": guildId})

    def delete(self, guildId: int) -> None:
        """Remove a guild settings document."""
        self.collection.delete_one({"_id": guildId})
        LOGGER.info("Removed settings for guild %s.", guildId)
