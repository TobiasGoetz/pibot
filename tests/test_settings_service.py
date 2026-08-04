"""Tests for SettingsService."""

from pibot.cogs.general.config import GeneralConfig
from pibot.cogs.summarize.config import SummarizeConfig
from pibot.guild_settings.serializer import fromStored
from pibot.guild_settings.service import SettingsService

GUILD_ID = 1


async def testDefaultsWithoutDocument(settingsService: SettingsService) -> None:
    """With no Mongo document, settings use model defaults."""
    # Act
    general = await settingsService.load(GUILD_ID, GeneralConfig)
    summarize = await settingsService.load(GUILD_ID, SummarizeConfig)
    generalDefaults = fromStored(GeneralConfig, {})
    summarizeDefaults = fromStored(SummarizeConfig, {})

    # Assert
    assert general.prefix == generalDefaults.prefix
    assert summarize.enabled == summarizeDefaults.enabled


async def testSetFeatureEnabledPersistsFalse(settingsService: SettingsService) -> None:
    """Disabling a feature persists through the service API."""
    # Act
    await settingsService.update(GUILD_ID, SummarizeConfig, "enabled", False)
    config = await settingsService.load(GUILD_ID, SummarizeConfig)

    # Assert
    assert config.enabled is False


async def testUnsetFeatureEnabledRestoresDefault(settingsService: SettingsService) -> None:
    """Resetting enabled restores the model default."""
    # Arrange
    await settingsService.update(GUILD_ID, SummarizeConfig, "enabled", False)

    # Act
    await settingsService.reset(GUILD_ID, SummarizeConfig, "enabled")
    config = await settingsService.load(GUILD_ID, SummarizeConfig)

    # Assert
    assert config.enabled is True


async def testSetPrefixPersists(settingsService: SettingsService) -> None:
    """Guild prefix persists through the service API."""
    # Act
    await settingsService.update(GUILD_ID, GeneralConfig, "prefix", "!")
    config = await settingsService.load(GUILD_ID, GeneralConfig)

    # Assert
    assert config.prefix == "!"


async def testUnsetPrefixRestoresDefault(settingsService: SettingsService) -> None:
    """Resetting prefix restores the model default."""
    # Arrange
    await settingsService.update(GUILD_ID, GeneralConfig, "prefix", "!")
    defaults = fromStored(GeneralConfig, {})

    # Act
    await settingsService.reset(GUILD_ID, GeneralConfig, "prefix")
    config = await settingsService.load(GUILD_ID, GeneralConfig)

    # Assert
    assert config.prefix == defaults.prefix


async def testUnsetCooldownRestoresDefault(settingsService: SettingsService) -> None:
    """Resetting a feature setting restores the model default."""
    # Arrange
    await settingsService.update(GUILD_ID, SummarizeConfig, "cooldownSeconds", 120)
    defaults = fromStored(SummarizeConfig, {})

    # Act
    await settingsService.reset(GUILD_ID, SummarizeConfig, "cooldownSeconds")
    config = await settingsService.load(GUILD_ID, SummarizeConfig)

    # Assert
    assert config.cooldownSeconds == defaults.cooldownSeconds


async def testSecondFeatureUpdatePreservesSiblings(settingsService: SettingsService) -> None:
    """Feature updates preserve sibling fields."""
    # Arrange
    await settingsService.update(GUILD_ID, SummarizeConfig, "cooldownSeconds", 120)

    # Act
    await settingsService.update(GUILD_ID, SummarizeConfig, "maxMessages", 500)
    config = await settingsService.load(GUILD_ID, SummarizeConfig)

    # Assert
    assert config.cooldownSeconds == 120
    assert config.maxMessages == 500


async def testUpdateReturnsUpdatedConfig(settingsService: SettingsService) -> None:
    """Update returns the persisted config without a follow-up read."""
    config = await settingsService.update(GUILD_ID, GeneralConfig, "prefix", "!")

    assert config.prefix == "!"


async def testResetReturnsDefaultConfig(settingsService: SettingsService) -> None:
    """Reset returns the config with model defaults applied."""
    await settingsService.update(GUILD_ID, GeneralConfig, "prefix", "!")
    defaults = fromStored(GeneralConfig, {})

    config = await settingsService.reset(GUILD_ID, GeneralConfig, "prefix")

    assert config.prefix == defaults.prefix


async def testGeneralUpdatePreservesSettingsGroup(settingsService: SettingsService) -> None:
    """Updating general settings does not wipe other feature settings."""
    # Arrange
    await settingsService.update(GUILD_ID, SummarizeConfig, "cooldownSeconds", 120)

    # Act
    await settingsService.update(GUILD_ID, GeneralConfig, "prefix", "!")
    summarize = await settingsService.load(GUILD_ID, SummarizeConfig)
    general = await settingsService.load(GUILD_ID, GeneralConfig)

    # Assert
    assert summarize.cooldownSeconds == 120
    assert general.prefix == "!"
