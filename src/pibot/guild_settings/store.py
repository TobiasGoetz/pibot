"""MongoDB persistence for per-guild settings."""

import logging
from typing import TypeVar

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
        return model.model_validate(section)

    def saveFeature(self, guildId: int, name: str, config: FeatureSettings) -> None:
        """Persist one feature section without touching other settings."""
        self.collection.update_one(
            {"_id": guildId},
            {"$set": {f"features.{name}": config.model_dump(mode="json")}},
            upsert=True,
        )
        LOGGER.info("Saved %s settings for guild %s.", name, guildId)

    def delete(self, guildId: int) -> None:
        """Remove a guild settings document."""
        self.collection.delete_one({"_id": guildId})
        LOGGER.info("Removed settings for guild %s.", guildId)
