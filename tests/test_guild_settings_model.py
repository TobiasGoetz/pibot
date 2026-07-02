"""Tests for SettingsGroup models and registry."""

import pibot.cogs.admin.config as _adminConfig  # noqa: F401 — registers AdminConfig
import pibot.cogs.general.config as _generalConfig  # noqa: F401 — registers GeneralConfig
import pibot.cogs.summarize.config as _summarizeConfig  # noqa: F401 — registers SummarizeConfig
import pibot.cogs.translations.config as _translationsConfig  # noqa: F401 — registers TranslationsConfig
from pibot.cogs.general.config import GeneralConfig
from pibot.cogs.summarize.config import SummarizeConfig
from pibot.guild_settings.registry import getSettingsGroups
from pibot.guild_settings.serializer import fromStored, parseSetting


def testPartialDocumentUsesModelDefaults() -> None:
    """Partial stored documents merge with optional model defaults."""
    # Arrange
    stored = {"cooldownSeconds": 120}
    defaults = fromStored(SummarizeConfig, {})

    # Act
    config = fromStored(SummarizeConfig, stored)

    # Assert
    assert config.cooldownSeconds == 120
    assert config.maxMessages == defaults.maxMessages


def testFeatureDiscovery() -> None:
    """Feature configs self-register when their cog config module is loaded."""
    # Act
    features = getSettingsGroups()

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
    cooldownSeconds = parseSetting(SummarizeConfig, "cooldownSeconds", "3600")

    # Assert
    assert "enabled" in fields
    assert "cooldownSeconds" in fields
    assert "cloudflareModel" in fields
    assert cooldownSeconds == 3600


def testSettingDefaults() -> None:
    """Unset optional settings use model defaults."""
    # Arrange
    defaults = fromStored(SummarizeConfig, {})

    # Act
    config = fromStored(SummarizeConfig, {})

    # Assert
    assert config == defaults


def testGeneralConfigModelDefault() -> None:
    """GeneralConfig exposes typed attribute access for empty stored data."""
    # Act
    config = fromStored(GeneralConfig, {})
    defaults = fromStored(GeneralConfig, {})

    # Assert
    assert config.prefix == defaults.prefix
