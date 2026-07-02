"""Tests for GuildSettingsService."""

from pibot.cogs.general.config import GeneralConfig
from pibot.cogs.summarize.config import SummarizeConfig
from pibot.guild_settings.serializer import fromStored
from pibot.guild_settings.service import GuildSettingsService

GUILD_ID = 1


async def testDefaultsWithoutDocument(guildSettingsService: GuildSettingsService) -> None:
    """With no Mongo document, settings use model defaults."""
    # Act
    general = await guildSettingsService.load(GUILD_ID, GeneralConfig)
    summarize = await guildSettingsService.load(GUILD_ID, SummarizeConfig)
    generalDefaults = fromStored(GeneralConfig, {})
    summarizeDefaults = fromStored(SummarizeConfig, {})

    # Assert
    assert general.prefix == generalDefaults.prefix
    assert summarize.enabled == summarizeDefaults.enabled


async def testSetFeatureEnabledPersistsFalse(guildSettingsService: GuildSettingsService) -> None:
    """Disabling a feature persists through the service API."""
    # Act
    await guildSettingsService.update(GUILD_ID, SummarizeConfig, "enabled", False)
    config = await guildSettingsService.load(GUILD_ID, SummarizeConfig)

    # Assert
    assert config.enabled is False


async def testUnsetFeatureEnabledRestoresDefault(guildSettingsService: GuildSettingsService) -> None:
    """Resetting enabled restores the model default."""
    # Arrange
    await guildSettingsService.update(GUILD_ID, SummarizeConfig, "enabled", False)

    # Act
    await guildSettingsService.reset(GUILD_ID, SummarizeConfig, "enabled")
    config = await guildSettingsService.load(GUILD_ID, SummarizeConfig)

    # Assert
    assert config.enabled is True


async def testSetPrefixPersists(guildSettingsService: GuildSettingsService) -> None:
    """Guild prefix persists through the service API."""
    # Act
    await guildSettingsService.update(GUILD_ID, GeneralConfig, "prefix", "!")
    config = await guildSettingsService.load(GUILD_ID, GeneralConfig)

    # Assert
    assert config.prefix == "!"


async def testUnsetPrefixRestoresDefault(guildSettingsService: GuildSettingsService) -> None:
    """Resetting prefix restores the model default."""
    # Arrange
    await guildSettingsService.update(GUILD_ID, GeneralConfig, "prefix", "!")
    defaults = fromStored(GeneralConfig, {})

    # Act
    await guildSettingsService.reset(GUILD_ID, GeneralConfig, "prefix")
    config = await guildSettingsService.load(GUILD_ID, GeneralConfig)

    # Assert
    assert config.prefix == defaults.prefix


async def testUnsetCooldownRestoresDefault(guildSettingsService: GuildSettingsService) -> None:
    """Resetting a feature setting restores the model default."""
    # Arrange
    await guildSettingsService.update(GUILD_ID, SummarizeConfig, "cooldownSeconds", 120)
    defaults = fromStored(SummarizeConfig, {})

    # Act
    await guildSettingsService.reset(GUILD_ID, SummarizeConfig, "cooldownSeconds")
    config = await guildSettingsService.load(GUILD_ID, SummarizeConfig)

    # Assert
    assert config.cooldownSeconds == defaults.cooldownSeconds


async def testSecondFeatureUpdatePreservesSiblings(guildSettingsService: GuildSettingsService) -> None:
    """Feature updates preserve sibling fields."""
    # Arrange
    await guildSettingsService.update(GUILD_ID, SummarizeConfig, "cooldownSeconds", 120)

    # Act
    await guildSettingsService.update(GUILD_ID, SummarizeConfig, "maxMessages", 500)
    config = await guildSettingsService.load(GUILD_ID, SummarizeConfig)

    # Assert
    assert config.cooldownSeconds == 120
    assert config.maxMessages == 500


async def testUpdateReturnsUpdatedConfig(guildSettingsService: GuildSettingsService) -> None:
    """Update returns the persisted config without a follow-up read."""
    config = await guildSettingsService.update(GUILD_ID, GeneralConfig, "prefix", "!")

    assert config.prefix == "!"


async def testResetReturnsDefaultConfig(guildSettingsService: GuildSettingsService) -> None:
    """Reset returns the config with model defaults applied."""
    await guildSettingsService.update(GUILD_ID, GeneralConfig, "prefix", "!")
    defaults = fromStored(GeneralConfig, {})

    config = await guildSettingsService.reset(GUILD_ID, GeneralConfig, "prefix")

    assert config.prefix == defaults.prefix


async def testGeneralUpdatePreservesSettingsGroup(guildSettingsService: GuildSettingsService) -> None:
    """Updating general settings does not wipe other feature settings."""
    # Arrange
    await guildSettingsService.update(GUILD_ID, SummarizeConfig, "cooldownSeconds", 120)

    # Act
    await guildSettingsService.update(GUILD_ID, GeneralConfig, "prefix", "!")
    summarize = await guildSettingsService.load(GUILD_ID, SummarizeConfig)
    general = await guildSettingsService.load(GUILD_ID, GeneralConfig)

    # Assert
    assert summarize.cooldownSeconds == 120
    assert general.prefix == "!"
