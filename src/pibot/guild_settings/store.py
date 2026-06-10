"""MongoDB persistence for per-guild settings."""

import logging

import pymongo

LOGGER = logging.getLogger("guild_settings.store")


class SettingsStore:
    """Thin MongoDB access layer for the discord.settings collection."""

    def __init__(self, client: pymongo.MongoClient) -> None:
        """Initialize collection handles."""
        self.collection = client["discord"]["settings"]

    def findById(self, guildId: int) -> dict | None:
        """Return the raw guild settings document, if present."""
        return self.collection.find_one({"_id": guildId})

    def setPath(self, guildId: int, dottedPath: str, value) -> None:
        """Set a nested field using MongoDB dotted path notation."""
        self.collection.update_one(
            {"_id": guildId},
            {"$set": {dottedPath: value}},
            upsert=True,
        )
        LOGGER.info("Updated %s for guild %s.", dottedPath, guildId)

    def unsetPath(self, guildId: int, dottedPath: str) -> None:
        """Remove a nested override so code defaults apply again."""
        self.collection.update_one(
            {"_id": guildId},
            {"$unset": {dottedPath: ""}},
        )
        LOGGER.info("Unset %s for guild %s.", dottedPath, guildId)

    def delete(self, guildId: int) -> None:
        """Remove a guild settings document."""
        self.collection.delete_one({"_id": guildId})
        LOGGER.info("Removed settings for guild %s.", guildId)
