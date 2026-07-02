"""Tests for SettingsStore MongoDB persistence."""

from pibot.cogs.summarize.config import SummarizeConfig
from pibot.guild_settings.store import SettingsStore

GUILD_ID = 1


async def testStoreSparseDumpOmitsDefaults(settingsStore: SettingsStore) -> None:
    """MongoDB stores only fields that differ from model defaults."""
    # Arrange
    config = SummarizeConfig(maxMessages=500)

    # Act
    await settingsStore.save(GUILD_ID, SummarizeConfig.name, config)
    raw = await settingsStore.collection.find_one({"_id": GUILD_ID})

    # Assert
    assert raw is not None
    assert raw["features"]["summarize"] == {"maxMessages": 500}


async def testStoreResetRemovesSettingsGroup(settingsStore: SettingsStore) -> None:
    """Resetting a field removes it from stored feature settings."""
    # Arrange
    await settingsStore.save(GUILD_ID, SummarizeConfig.name, SummarizeConfig(maxMessages=500))

    # Act
    await settingsStore.resetField(GUILD_ID, SummarizeConfig.name, "maxMessages")
    raw = await settingsStore.collection.find_one({"_id": GUILD_ID})

    # Assert
    assert raw is None or "summarize" not in raw.get("features", {})


async def testStoreSetDefaultRemovesField(settingsStore: SettingsStore) -> None:
    """Setting a field back to its default removes it from MongoDB."""
    # Arrange
    await settingsStore.save(
        GUILD_ID,
        SummarizeConfig.name,
        SummarizeConfig(maxMessages=500, cooldownSeconds=120),
    )

    # Act
    await settingsStore.save(
        GUILD_ID,
        SummarizeConfig.name,
        SummarizeConfig(cooldownSeconds=120),
    )
    raw = await settingsStore.collection.find_one({"_id": GUILD_ID})

    # Assert
    assert raw is not None
    assert raw["features"]["summarize"] == {"cooldownSeconds": 120}
