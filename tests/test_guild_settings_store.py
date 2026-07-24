"""Tests for SettingsStore MongoDB persistence."""

from pibot.cogs.summarize.config import SummarizeConfig
from pibot.guild_settings.store import SettingsStore

GUILD_ID = 1


async def testStoreSetFieldPersistsOneField(settingsStore: SettingsStore) -> None:
    """Field-scoped writes store only the changed field."""
    # Act
    await settingsStore.setField(GUILD_ID, SummarizeConfig.name, "maxMessages", 500)
    raw = await settingsStore.collection.find_one({"_id": GUILD_ID})

    # Assert
    assert raw is not None
    assert raw["features"]["summarize"] == {"maxMessages": 500}


async def testStoreSetFieldPreservesSiblingFields(settingsStore: SettingsStore) -> None:
    """Field-scoped writes do not replace sibling fields in the same group."""
    # Arrange
    await settingsStore.setField(GUILD_ID, SummarizeConfig.name, "cooldownSeconds", 120)

    # Act
    await settingsStore.setField(GUILD_ID, SummarizeConfig.name, "maxMessages", 500)
    raw = await settingsStore.collection.find_one({"_id": GUILD_ID})

    # Assert
    assert raw is not None
    assert raw["features"]["summarize"] == {"cooldownSeconds": 120, "maxMessages": 500}


async def testStoreUnsetFieldLeavesEmptyGroupShell(settingsStore: SettingsStore) -> None:
    """Unset on the last stored field leaves an empty group object."""
    # Arrange
    await settingsStore.setField(GUILD_ID, SummarizeConfig.name, "maxMessages", 500)

    # Act
    await settingsStore.unsetField(GUILD_ID, SummarizeConfig.name, "maxMessages")
    raw = await settingsStore.collection.find_one({"_id": GUILD_ID})

    # Assert
    assert raw is not None
    assert raw["features"]["summarize"] == {}


async def testStoreUnsetFieldPreservesSiblingFields(settingsStore: SettingsStore) -> None:
    """Unset removes only the targeted field."""
    # Arrange
    await settingsStore.setField(GUILD_ID, SummarizeConfig.name, "cooldownSeconds", 120)
    await settingsStore.setField(GUILD_ID, SummarizeConfig.name, "maxMessages", 500)

    # Act
    await settingsStore.unsetField(GUILD_ID, SummarizeConfig.name, "maxMessages")
    raw = await settingsStore.collection.find_one({"_id": GUILD_ID})

    # Assert
    assert raw is not None
    assert raw["features"]["summarize"] == {"cooldownSeconds": 120}
