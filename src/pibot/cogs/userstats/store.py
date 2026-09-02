"""MongoDB persistence for per-member activity stats."""

import logging

import discord
from pymongo import AsyncMongoClient

from pibot.cogs.userstats.model import UserStatsRecord

LOGGER = logging.getLogger("userstats.store")


class UserstatsStore:
    """MongoDB access layer for the discord.userstats collection."""

    def __init__(self, client: AsyncMongoClient) -> None:
        """Initialize collection handles."""
        self.collection = client["discord"]["userstats"]

    async def ensureIndexes(self) -> None:
        """Create indexes required for guild-scoped queries and leaderboards."""
        await self.collection.create_index(
            [("_id.guildId", 1), ("messageCount", -1)],
            name="guild_message_count",
        )
        LOGGER.debug("Ensured userstats indexes.")

    async def recordMessage(self, message: discord.Message) -> None:
        """Increment message stats for the message author."""
        guild = message.guild
        if guild is None:
            return

        sentAt = message.created_at
        await self.collection.update_one(
            {"_id": {"guildId": guild.id, "userId": message.author.id}},
            {
                "$inc": {"messageCount": 1},
                "$set": {"lastMessageAt": sentAt},
                "$setOnInsert": {"firstSeenAt": sentAt},
            },
            upsert=True,
        )
        LOGGER.debug(
            "Recorded userstats: guild=%s user=%s channel=%s message=%s sentAt=%s",
            guild.id,
            message.author.id,
            message.channel.id,
            message.id,
            sentAt,
        )

    async def getStats(self, guildId: int, userId: int) -> UserStatsRecord | None:
        """Load activity stats for one guild member."""
        doc = await self.collection.find_one({"_id": {"guildId": guildId, "userId": userId}})
        return UserStatsRecord.fromDocument(doc)
