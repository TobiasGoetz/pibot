"""Tests for per-guild settings."""

import copy

import pytest
from pydantic import SecretStr

from pibot.cogs.summarize.config import COOLDOWN_SECONDS, MAX_MESSAGES, SummarizeConfig
from pibot.guild_settings.config import GuildConfig
from pibot.guild_settings.general import DEFAULT_PREFIX
from pibot.guild_settings.model import getFeatures, getSettings
from pibot.guild_settings.service import GuildSettingsService
from pibot.guild_settings.store import SettingsStore


class FakeCollection:
    """In-memory MongoDB collection stub."""

    def __init__(self) -> None:
        """Initialize an empty in-memory collection."""
        self.docs: dict[int, dict] = {}

    def find_one(self, query: dict) -> dict | None:
        """Return a stored document by ``_id``."""
        if "_id" in query:
            return copy.deepcopy(self.docs.get(query["_id"]))
        return None

    def replace_one(self, query: dict, document: dict, upsert: bool = False) -> None:
        """Replace a stored document."""
        guildId = query["_id"]
        self.docs[guildId] = copy.deepcopy(document)

    def delete_one(self, query: dict) -> None:
        """Delete a stored document."""
        self.docs.pop(query["_id"], None)


class FakeSettingsStore(SettingsStore):
    """Settings store backed by in-memory collections."""

    def __init__(self) -> None:
        """Initialize with a fake MongoDB collection."""
        self.collection = FakeCollection()


@pytest.fixture
def service() -> GuildSettingsService:
    """Guild settings service with a fake store."""
    return GuildSettingsService(FakeSettingsStore())


def testDefaultsWithoutDocument(service: GuildSettingsService) -> None:
    """With no Mongo document, settings use model defaults."""
    assert service.store.findById(1) is None
    assert service.get(1).general.prefix == DEFAULT_PREFIX
    assert service.get(1).features.summarize.enabled is True


def testFeatureEnabledOptOut(service: GuildSettingsService) -> None:
    """Feature enabled flag persists via Pydantic round-trip."""
    assert service.get(2).features.summarize.enabled is True
    service.setFeatureSetting(2, SummarizeConfig, "enabled", False)
    assert service.get(2).features.summarize.enabled is False
    stored = service.store.findById(2)
    assert stored is not None
    assert stored.features.summarize.enabled is False

    service.unsetFeatureSetting(2, SummarizeConfig, "enabled")
    assert service.get(2).features.summarize.enabled is True


def testSetAndResetPrefix(service: GuildSettingsService) -> None:
    """Guild prefix persists and resets to the model default."""
    service.setPrefix(3, "!")
    assert service.get(3).general.prefix == "!"
    stored = service.store.findById(3)
    assert stored is not None
    assert stored.general.prefix == "!"

    service.unsetPrefix(3)
    assert service.get(3).general.prefix == DEFAULT_PREFIX


def testResetFeatureSettingRestoresDefault(service: GuildSettingsService) -> None:
    """Resetting a feature setting restores the model default."""
    service.setFeatureSetting(4, SummarizeConfig, "cooldownSeconds", 120)
    assert service.get(4).features.summarize.cooldownSeconds == 120

    service.unsetFeatureSetting(4, SummarizeConfig, "cooldownSeconds")
    assert service.get(4).features.summarize.cooldownSeconds == COOLDOWN_SECONDS


def testNestedFeatureSettingPreservesSiblings(service: GuildSettingsService) -> None:
    """Feature updates preserve sibling fields."""
    service.setFeatureSetting(6, SummarizeConfig, "cooldownSeconds", 120)
    service.setFeatureSetting(6, SummarizeConfig, "cloudflareBaseUrl", "https://example.com")
    config = service.get(6)
    assert config.features.summarize.cooldownSeconds == 120
    assert config.features.summarize.cloudflareBaseUrl == "https://example.com"
    assert config.features.summarize.maxMessages == MAX_MESSAGES


def testGuildConfigTypedAccess(service: GuildSettingsService) -> None:
    """GuildConfig exposes nested typed attribute access."""
    config = service.get(1)
    assert config.features.summarize.cloudflareBaseUrl == ""
    assert config.features.summarize.cooldownSeconds == COOLDOWN_SECONDS


def testPartialDocumentUsesModelDefaults() -> None:
    """Pydantic fills missing fields when loading a partial stored document."""
    config = GuildConfig.fromDocument({"features": {"summarize": {"cooldownSeconds": 120}}})
    assert config.features.summarize.cooldownSeconds == 120
    assert config.features.summarize.maxMessages == MAX_MESSAGES
    assert config.general.prefix == DEFAULT_PREFIX


def testFeatureDiscovery() -> None:
    """Feature configs self-register from cogs/*/config.py."""
    features = getFeatures()
    assert "summarize" in features
    assert "translations" in features
    assert features["summarize"].description


def testSettingRegistration() -> None:
    """Configurable fields register from the feature model."""
    fields = [field for field, _ in getSettings(SummarizeConfig)]
    assert "enabled" in fields
    assert "cooldownSeconds" in fields
    assert "cloudflareBaseUrl" in fields
    assert SummarizeConfig.parseSetting("cooldownSeconds", "3600") == 3600


def testSettingDefaults() -> None:
    """Unset settings use model field defaults."""
    from pibot.cogs.summarize.config import DEFAULT_MODEL

    config = GuildConfig().features.summarize
    assert config.cooldownSeconds == COOLDOWN_SECONDS
    assert config.maxMessages == MAX_MESSAGES
    assert config.cloudflareBaseUrl == ""
    assert config.cloudflareModel == DEFAULT_MODEL
    assert config.configured is False


def testLegacyCloudflareGroupMigratesOnLoad() -> None:
    """Nested cloudflare documents from older configs migrate to flat fields."""
    config = SummarizeConfig.model_validate(
        {
            "cloudflare": {
                "baseUrl": "https://example.com",
                "token": "secret",
                "model": "test-model",
            }
        }
    )
    assert config.cloudflareBaseUrl == "https://example.com"
    assert config.cloudflareToken.get_secret_value() == "secret"
    assert config.cloudflareModel == "test-model"


def testSecretStrMasksDisplay() -> None:
    """SecretStr values are masked for display."""
    assert str(SecretStr("abcd")) == "**********"
