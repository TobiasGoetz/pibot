"""Tests for per-guild settings."""

from pibot.cogs.admin import config as _adminConfig  # noqa: F401 — registers AdminConfig
from pibot.cogs.general.config import DEFAULT_PREFIX, GeneralConfig
from pibot.cogs.general import config as _generalConfig  # noqa: F401 — registers GeneralConfig
from pibot.cogs.summarize.config import COOLDOWN_SECONDS, DEFAULT_MODEL, MAX_MESSAGES, SummarizeConfig
from pibot.cogs.translations import config as _translationsConfig  # noqa: F401 — registers TranslationsConfig
from pibot.guild_settings.model import getFeatures
from pibot.guild_settings.service import GuildSettingsService

GUILD_ID = 1


# --- GuildSettingsService ---


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


# --- SettingsStore persistence ---


async def testStoreSparseDumpOmitsDefaults(guildSettingsService: GuildSettingsService) -> None:
    """MongoDB stores only fields that differ from model defaults."""
    # Arrange
    store = guildSettingsService.store

    # Act
    await guildSettingsService.setFeatureField(GUILD_ID, SummarizeConfig, "maxMessages", 500)
    raw = await store.collection.find_one({"_id": GUILD_ID})

    # Assert
    assert raw is not None
    assert raw["features"]["summarize"] == {"maxMessages": 500}


async def testStoreUnsetRemovesFeatureSection(guildSettingsService: GuildSettingsService) -> None:
    """Resetting a field removes it from stored feature settings."""
    # Arrange
    store = guildSettingsService.store
    await guildSettingsService.setFeatureField(GUILD_ID, SummarizeConfig, "maxMessages", 500)

    # Act
    await guildSettingsService.unsetFeatureField(GUILD_ID, SummarizeConfig, "maxMessages")
    raw = await store.collection.find_one({"_id": GUILD_ID})

    # Assert
    assert raw is None or "summarize" not in raw.get("features", {})


async def testStoreSetDefaultRemovesField(guildSettingsService: GuildSettingsService) -> None:
    """Setting a field back to its default removes it from MongoDB."""
    # Arrange
    store = guildSettingsService.store
    await guildSettingsService.setFeatureField(GUILD_ID, SummarizeConfig, "maxMessages", 500)
    await guildSettingsService.setFeatureField(GUILD_ID, SummarizeConfig, "cooldownSeconds", 120)

    # Act
    await guildSettingsService.setFeatureField(GUILD_ID, SummarizeConfig, "maxMessages", MAX_MESSAGES)
    raw = await store.collection.find_one({"_id": GUILD_ID})

    # Assert
    assert raw is not None
    assert raw["features"]["summarize"] == {"cooldownSeconds": 120}


# --- FeatureSettings models ---


def testPartialDocumentUsesModelDefaults() -> None:
    """Partial stored documents merge with optional model defaults."""
    # Arrange
    stored = {"cooldownSeconds": 120}

    # Act
    config = SummarizeConfig.fromStored(stored)

    # Assert
    assert config.cooldownSeconds == 120
    assert config.maxMessages == MAX_MESSAGES


def testFeatureDiscovery() -> None:
    """Feature configs self-register from cogs/*/config.py."""
    # Act
    features = getFeatures()

    # Assert
    assert "general" in features
    assert "admin" in features
    assert "summarize" in features
    assert "translations" in features
    assert features["summarize"].description


def testSettingRegistration() -> None:
    """Configurable fields register from the feature model."""
    # Act
    fields = list(SummarizeConfig.model_fields)
    cooldownSeconds = SummarizeConfig.parseSetting("cooldownSeconds", "3600")

    # Assert
    assert "enabled" in fields
    assert "cooldownSeconds" in fields
    assert "cloudflareModel" in fields
    assert cooldownSeconds == 3600


def testSettingDefaults() -> None:
    """Unset optional settings use model defaults."""
    # Act
    config = SummarizeConfig.fromStored({})

    # Assert
    assert config.cooldownSeconds == COOLDOWN_SECONDS
    assert config.maxMessages == MAX_MESSAGES
    assert config.cloudflareModel == DEFAULT_MODEL


def testGeneralConfigModelDefault() -> None:
    """GeneralConfig exposes typed attribute access for empty stored data."""
    # Act
    config = GeneralConfig.model_validate({})

    # Assert
    assert config.prefix == DEFAULT_PREFIX
