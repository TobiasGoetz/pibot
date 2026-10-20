"""Tests for userstats cog helpers."""

import discord
import pytest

from pibot.cogs.userstats.cog import isTrackedPresenceChange


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (discord.Status.offline, discord.Status.online, True),
        (discord.Status.online, discord.Status.offline, True),
        (discord.Status.idle, discord.Status.offline, True),
        (discord.Status.dnd, discord.Status.online, True),
        (discord.Status.idle, discord.Status.online, True),
        (discord.Status.online, discord.Status.idle, False),
        (discord.Status.online, discord.Status.dnd, False),
        (discord.Status.idle, discord.Status.dnd, False),
        (discord.Status.dnd, discord.Status.idle, False),
        (discord.Status.online, discord.Status.online, False),
        (discord.Status.offline, discord.Status.offline, False),
        (discord.Status.idle, discord.Status.idle, False),
    ],
)
def testIsTrackedPresenceChange(
    before: discord.Status,
    after: discord.Status,
    expected: bool,
) -> None:
    """Last seen updates only when the new status is online or offline."""
    # Act
    result = isTrackedPresenceChange(before, after)

    # Assert
    assert result is expected
