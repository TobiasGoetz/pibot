"""MongoDB persistence for per-guild settings."""

import logging
from datetime import UTC, datetime

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

    def ensureGuild(self, guildId: int, name: str) -> None:
        """Ensure a guild document exists (metadata only; settings are sparse overrides)."""
        now = datetime.now(UTC)
        self.collection.update_one(
            {"_id": guildId},
            {
                "$set": {"name": name, "updatedAt": now},
                "$setOnInsert": {"_id": guildId},
            },
            upsert=True,
        )

    def setPath(self, guildId: int, dottedPath: str, value) -> None:
        """Set a nested field using MongoDB dotted path notation."""
        now = datetime.now(UTC)
        self.collection.update_one(
            {"_id": guildId},
            {"$set": {dottedPath: value, "updatedAt": now}},
        )
        LOGGER.info("Updated %s for guild %s.", dottedPath, guildId)

    def unsetPath(self, guildId: int, dottedPath: str) -> None:
        """Remove a nested override so code defaults apply again."""
        now = datetime.now(UTC)
        self.collection.update_one(
            {"_id": guildId},
            {"$unset": {dottedPath: ""}, "$set": {"updatedAt": now}},
        )
        LOGGER.info("Unset %s for guild %s.", dottedPath, guildId)

    def setName(self, guildId: int, name: str) -> None:
        """Update the denormalized guild name."""
        now = datetime.now(UTC)
        self.collection.update_one(
            {"_id": guildId},
            {"$set": {"name": name, "updatedAt": now}},
        )

    def delete(self, guildId: int) -> None:
        """Remove a guild settings document."""
        self.collection.delete_one({"_id": guildId})
        LOGGER.info("Removed settings for guild %s.", guildId)
