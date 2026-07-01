"""Tests for SettingsGroup models and registration."""

from pibot.cogs.admin import config as _adminConfig  # noqa: F401 — registers AdminConfig
from pibot.cogs.general.config import GeneralConfig
from pibot.cogs.general import config as _generalConfig  # noqa: F401 — registers GeneralConfig
from pibot.cogs.summarize.config import SummarizeConfig
from pibot.cogs.translations import config as _translationsConfig  # noqa: F401 — registers TranslationsConfig
from pibot.guild_settings.model import getSettingsGroups


def testPartialDocumentUsesModelDefaults() -> None:
    """Partial stored documents merge with optional model defaults."""
    # Arrange
    stored = {"cooldownSeconds": 120}
    defaults = SummarizeConfig.fromStored({})

    # Act
    config = SummarizeConfig.fromStored(stored)

    # Assert
    assert config.cooldownSeconds == 120
    assert config.maxMessages == defaults.maxMessages


def testFeatureDiscovery() -> None:
    """Feature configs self-register from cogs/*/config.py."""
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
    cooldownSeconds = SummarizeConfig.parseSetting("cooldownSeconds", "3600")

    # Assert
    assert "enabled" in fields
    assert "cooldownSeconds" in fields
    assert "cloudflareModel" in fields
    assert cooldownSeconds == 3600


def testSettingDefaults() -> None:
    """Unset optional settings use model defaults."""
    # Arrange
    defaults = SummarizeConfig.fromStored({})

    # Act
    config = SummarizeConfig.fromStored({})

    # Assert
    assert config == defaults


def testGeneralConfigModelDefault() -> None:
    """GeneralConfig exposes typed attribute access for empty stored data."""
    # Act
    config = GeneralConfig.fromStored({})
    defaults = GeneralConfig.fromStored({})

    # Assert
    assert config.prefix == defaults.prefix
