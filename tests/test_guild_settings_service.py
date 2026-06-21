"""Tests for GuildSettingsService."""

from pibot.cogs.admin import config as _adminConfig  # noqa: F401 — registers AdminConfig
from pibot.cogs.general.config import DEFAULT_PREFIX, GeneralConfig
from pibot.cogs.general import config as _generalConfig  # noqa: F401 — registers GeneralConfig
from pibot.cogs.summarize.config import COOLDOWN_SECONDS, SummarizeConfig
from pibot.cogs.translations import config as _translationsConfig  # noqa: F401 — registers TranslationsConfig
from pibot.guild_settings.service import GuildSettingsService

GUILD_ID = 1


async def testDefaultsWithoutDocument(guildSettingsService: GuildSettingsService) -> None:
    """With no Mongo document, settings use model defaults."""
    # Act
    general = await guildSettingsService.getFeature(GUILD_ID, GeneralConfig)
    summarize = await guildSettingsService.getFeature(GUILD_ID, SummarizeConfig)

    # Assert
    assert general.prefix == DEFAULT_PREFIX
    assert summarize.enabled is True


async def testSetFeatureEnabledPersistsFalse(guildSettingsService: GuildSettingsService) -> None:
    """Disabling a feature persists through the service API."""
    # Act
    await guildSettingsService.setFeatureField(GUILD_ID, SummarizeConfig, "enabled", False)
    config = await guildSettingsService.getFeature(GUILD_ID, SummarizeConfig)

    # Assert
    assert config.enabled is False


async def testUnsetFeatureEnabledRestoresDefault(guildSettingsService: GuildSettingsService) -> None:
    """Resetting enabled restores the model default."""
    # Arrange
    await guildSettingsService.setFeatureField(GUILD_ID, SummarizeConfig, "enabled", False)

    # Act
    await guildSettingsService.unsetFeatureField(GUILD_ID, SummarizeConfig, "enabled")
    config = await guildSettingsService.getFeature(GUILD_ID, SummarizeConfig)

    # Assert
    assert config.enabled is True


async def testSetPrefixPersists(guildSettingsService: GuildSettingsService) -> None:
    """Guild prefix persists through the service API."""
    # Act
    await guildSettingsService.setFeatureField(GUILD_ID, GeneralConfig, "prefix", "!")
    config = await guildSettingsService.getFeature(GUILD_ID, GeneralConfig)

    # Assert
    assert config.prefix == "!"


async def testUnsetPrefixRestoresDefault(guildSettingsService: GuildSettingsService) -> None:
    """Resetting prefix restores the model default."""
    # Arrange
    await guildSettingsService.setFeatureField(GUILD_ID, GeneralConfig, "prefix", "!")

    # Act
    await guildSettingsService.unsetFeatureField(GUILD_ID, GeneralConfig, "prefix")
    config = await guildSettingsService.getFeature(GUILD_ID, GeneralConfig)

    # Assert
    assert config.prefix == DEFAULT_PREFIX


async def testUnsetCooldownRestoresDefault(guildSettingsService: GuildSettingsService) -> None:
    """Resetting a feature setting restores the model default."""
    # Arrange
    await guildSettingsService.setFeatureField(GUILD_ID, SummarizeConfig, "cooldownSeconds", 120)

    # Act
    await guildSettingsService.unsetFeatureField(GUILD_ID, SummarizeConfig, "cooldownSeconds")
    config = await guildSettingsService.getFeature(GUILD_ID, SummarizeConfig)

    # Assert
    assert config.cooldownSeconds == COOLDOWN_SECONDS


async def testSecondFeatureUpdatePreservesSiblings(guildSettingsService: GuildSettingsService) -> None:
    """Feature updates preserve sibling fields."""
    # Arrange
    await guildSettingsService.setFeatureField(GUILD_ID, SummarizeConfig, "cooldownSeconds", 120)

    # Act
    await guildSettingsService.setFeatureField(GUILD_ID, SummarizeConfig, "maxMessages", 500)
    config = await guildSettingsService.getFeature(GUILD_ID, SummarizeConfig)

    # Assert
    assert config.cooldownSeconds == 120
    assert config.maxMessages == 500


async def testGeneralUpdatePreservesFeatureSection(guildSettingsService: GuildSettingsService) -> None:
    """Updating general settings does not wipe feature sections."""
    # Arrange
    await guildSettingsService.setFeatureField(GUILD_ID, SummarizeConfig, "cooldownSeconds", 120)

    # Act
    await guildSettingsService.setFeatureField(GUILD_ID, GeneralConfig, "prefix", "!")
    summarize = await guildSettingsService.getFeature(GUILD_ID, SummarizeConfig)
    general = await guildSettingsService.getFeature(GUILD_ID, GeneralConfig)

    # Assert
    assert summarize.cooldownSeconds == 120
    assert general.prefix == "!"
