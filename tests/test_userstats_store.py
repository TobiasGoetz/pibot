"""Tests for UserstatsStore MongoDB persistence."""

from datetime import UTC, datetime
from types import SimpleNamespace

from pibot.cogs.userstats.store import UserstatsStore

GUILD_ID = 1
USER_ID = 42
SENT_AT = datetime(2026, 9, 2, 8, 30, tzinfo=UTC)


def _message(*, guildId: int = GUILD_ID, userId: int = USER_ID, sentAt: datetime = SENT_AT) -> SimpleNamespace:
    """Build a minimal message stand-in for store tests."""
    return SimpleNamespace(
        guild=SimpleNamespace(id=guildId),
        author=SimpleNamespace(id=userId),
        channel=SimpleNamespace(id=99),
        id=123456789,
        created_at=sentAt,
    )


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
