"""Tests for UserstatsStore MongoDB persistence."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import discord

from pibot.cogs.userstats.store import UserstatsStore

GUILD_ID = 1
USER_ID = 42
CHANNEL_ID = 99
SENT_AT = datetime(2026, 9, 2, 8, 30, tzinfo=UTC)


def _payload(data: dict[str, Any]) -> Any:
    """Partial gateway payload. Constructors accept incomplete dicts at runtime."""
    return data


def _userPayload(userId: int = USER_ID) -> dict[str, Any]:
    """Build a gateway user payload for store tests."""
    return {
        "id": userId,
        "username": "tester",
        "discriminator": "0",
        "avatar": None,
        "global_name": None,
        "bot": False,
    }


def _guild(state: Any, guildId: int = GUILD_ID) -> discord.Guild:
    """Build a guild model for store tests."""
    return discord.Guild(state=state, data=_payload({"id": guildId}))


def _message(*, guildId: int = GUILD_ID, userId: int = USER_ID, sentAt: datetime = SENT_AT) -> discord.Message:
    """Build a message model for store tests."""
    state: Any = MagicMock()
    state.store_user.return_value.id = userId
    channel = discord.TextChannel(
        state=state,
        guild=_guild(state, guildId),
        data=_payload(
            {
                "id": CHANNEL_ID,
                "type": 0,
                "name": "general",
                "position": 0,
                "guild_id": guildId,
                "permission_overwrites": [],
                "nsfw": False,
                "parent_id": None,
            }
        ),
    )
    return discord.Message(
        state=state,
        channel=channel,
        data=_payload(
            {
                "id": discord.utils.time_snowflake(sentAt),
                "channel_id": CHANNEL_ID,
                "type": 0,
                "content": "",
                "author": _userPayload(userId),
                "attachments": [],
                "embeds": [],
                "mentions": [],
                "mention_roles": [],
                "pinned": False,
                "mention_everyone": False,
                "tts": False,
                "edited_timestamp": None,
                "timestamp": sentAt.isoformat(),
            }
        ),
    )


def _member(*, guildId: int = GUILD_ID, userId: int = USER_ID) -> discord.Member:
    """Build a member model for store tests."""
    state: Any = MagicMock()
    state.store_user.return_value.id = userId
    member = discord.Member(
        data=_payload(
            {
                "user": _userPayload(userId),
                "roles": [],
                "joined_at": None,
                "deaf": False,
                "mute": False,
                "flags": 0,
            }
        ),
        guild=_guild(state, guildId),
        state=state,
    )
    member.status = discord.Status.online
    return member


async def testRecordMessageCreatesDocument(userstatsStore: UserstatsStore) -> None:
    """First message creates a stats document with initial counters."""
    # Act
    await userstatsStore.recordMessage(_message())
    raw = await userstatsStore.collection.find_one({"_id": {"guildId": GUILD_ID, "userId": USER_ID}})

    # Assert
    assert raw is not None
    assert raw["messageCount"] == 1
    assert raw["lastMessageAt"] == SENT_AT
    assert "firstSeenAt" not in raw


async def testRecordMessageIncrementsCount(userstatsStore: UserstatsStore) -> None:
    """Repeated messages increment the counter and update last message time."""
    # Arrange
    later = datetime(2026, 9, 2, 9, 0, tzinfo=UTC)
    await userstatsStore.recordMessage(_message())

    # Act
    await userstatsStore.recordMessage(_message(sentAt=later))
    record = await userstatsStore.getStats(GUILD_ID, USER_ID)

    # Assert
    assert record is not None
    assert record.messageCount == 2
    assert record.lastMessageAt == later


async def testRecordPresenceSetsLastSeenAt(userstatsStore: UserstatsStore) -> None:
    """Presence updates create or update last seen time."""
    # Arrange
    seenAt = datetime(2026, 9, 2, 10, 0, tzinfo=UTC)

    # Act
    await userstatsStore.recordPresence(_member(), seenAt)
    record = await userstatsStore.getStats(GUILD_ID, USER_ID)

    # Assert
    assert record is not None
    assert record.messageCount == 0
    assert record.lastSeenAt == seenAt
    assert record.lastMessageAt is None


async def testGetStatsReturnsNoneWhenMissing(userstatsStore: UserstatsStore) -> None:
    """Missing members return no record."""
    # Act
    record = await userstatsStore.getStats(GUILD_ID, USER_ID)

    # Assert
    assert record is None


async def testEnsureIndexesCreatesGuildMessageCountIndex(userstatsStore: UserstatsStore) -> None:
    """Startup index creation adds the guild leaderboard index."""
    # Act
    await userstatsStore.ensureIndexes()
    indexes = await userstatsStore.collection.index_information()

    # Assert
    assert "guild_message_count" in indexes
    assert indexes["guild_message_count"]["key"] == [("_id.guildId", 1), ("messageCount", -1)]
