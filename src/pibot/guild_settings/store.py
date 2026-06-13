"""MongoDB persistence for per-guild settings."""

import logging

import pymongo

from pibot.guild_settings.config import GuildConfig

LOGGER = logging.getLogger("guild_settings.store")


class SettingsStore:
    """MongoDB access layer for the discord.settings collection."""

    def __init__(self, client: pymongo.MongoClient) -> None:
        """Initialize collection handles."""
        self.collection = client["discord"]["settings"]

    def findById(self, guildId: int) -> GuildConfig | None:
        """Return guild settings, if present."""
        raw = self.collection.find_one({"_id": guildId})
        if raw is None:
            return None
        payload = {key: raw[key] for key in ("general", "features") if key in raw}
        return GuildConfig.fromDocument(payload)

    def save(self, guildId: int, config: GuildConfig) -> None:
        """Persist guild settings."""
        document = config.toDocument()
        document["_id"] = guildId
        self.collection.replace_one({"_id": guildId}, document, upsert=True)
        LOGGER.info("Saved settings for guild %s.", guildId)

    def delete(self, guildId: int) -> None:
        """Remove a guild settings document."""
        self.collection.delete_one({"_id": guildId})
        LOGGER.info("Removed settings for guild %s.", guildId)
