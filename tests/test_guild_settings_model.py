"""Tests for SettingsGroup models and registry."""

import pytest

from pydantic import Field

from pibot.cogs.admin.config import AdminConfig
from pibot.cogs.general.config import GeneralConfig
from pibot.cogs.summarize.config import SummarizeConfig
from pibot.cogs.translations.config import TranslationsConfig
from pibot.guild_settings.errors import InvalidSettingValue
from pibot.guild_settings.model import SettingsGroup
from pibot.guild_settings.registry import getSettingsGroups
from pibot.guild_settings.serializer import fromStored, parseModalSetting, parseSetting


class RequiredFieldConfig(SettingsGroup):
    """Synthetic config with one required field."""

    name = "required-field"
    description = "Test config"

    token: str = Field(description="Required token")


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
    assert features["general"] is GeneralConfig
    assert features["admin"] is AdminConfig
    assert features["summarize"] is SummarizeConfig
    assert features["translations"] is TranslationsConfig
    assert features["summarize"].description


def testParseModalSettingUsesDefaultForEmptyOptional() -> None:
    """Empty modal input resets optional settings to the model default."""
    assert parseModalSetting(GeneralConfig, "prefix", "") == "."


def testParseModalSettingRejectsEmptyRequired() -> None:
    """Empty modal input is rejected for required settings."""
    with pytest.raises(InvalidSettingValue, match="token is required"):
        parseModalSetting(RequiredFieldConfig, "token", "")


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
