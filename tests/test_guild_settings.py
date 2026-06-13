"""Tests for per-guild settings."""

import copy

import pytest
from pydantic import SecretStr

from pibot.cogs.admin import config as _adminConfig  # noqa: F401 — registers AdminConfig
from pibot.cogs.general.config import DEFAULT_PREFIX, GeneralConfig
from pibot.cogs.general import config as _generalConfig  # noqa: F401 — registers GeneralConfig
from pibot.cogs.summarize.config import COOLDOWN_SECONDS, MAX_MESSAGES, SummarizeConfig
from pibot.cogs.translations import config as _translationsConfig  # noqa: F401 — registers TranslationsConfig
from pibot.guild_settings.model import getFeatures
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

    def update_one(self, query: dict, update: dict, upsert: bool = False) -> None:
        """Apply a partial update to a stored document."""
        guildId = query["_id"]
        document = copy.deepcopy(self.docs.get(guildId, {"_id": guildId}))
        for key, value in update.get("$set", {}).items():
            if "." in key:
                section, field = key.split(".", 1)
                document.setdefault(section, {})[field] = copy.deepcopy(value)
            else:
                document[key] = copy.deepcopy(value)
        for key in update.get("$unset", {}):
            if "." in key:
                section, field = key.split(".", 1)
                sectionDict = document.get(section)
                if isinstance(sectionDict, dict):
                    sectionDict.pop(field, None)
                    if not sectionDict:
                        document.pop(section, None)
            else:
                document.pop(key, None)
        self.docs[guildId] = document

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
    assert service.getFeature(1, GeneralConfig).prefix == DEFAULT_PREFIX
    assert service.getFeature(1, SummarizeConfig).enabled is True


def testFeatureEnabledOptOut(service: GuildSettingsService) -> None:
    """Feature enabled flag persists via Pydantic round-trip."""
    assert service.getFeature(2, SummarizeConfig).enabled is True
    service.setFeatureField(2, SummarizeConfig, "enabled", False)
    assert service.getFeature(2, SummarizeConfig).enabled is False
    stored = service.store.findFeature(2, SummarizeConfig.name, SummarizeConfig)
    assert stored.enabled is False

    service.unsetFeatureField(2, SummarizeConfig, "enabled")
    assert service.getFeature(2, SummarizeConfig).enabled is True


def testSetAndResetPrefix(service: GuildSettingsService) -> None:
    """Guild prefix persists and resets to the model default."""
    service.setFeatureField(3, GeneralConfig, "prefix", "!")
    assert service.getFeature(3, GeneralConfig).prefix == "!"
    stored = service.store.findFeature(3, GeneralConfig.name, GeneralConfig)
    assert stored.prefix == "!"

    service.unsetFeatureField(3, GeneralConfig, "prefix")
    assert service.getFeature(3, GeneralConfig).prefix == DEFAULT_PREFIX


def testSparseStorageOmitsDefaults(service: GuildSettingsService) -> None:
    """MongoDB stores only fields that differ from model defaults."""
    service.setFeatureField(5, SummarizeConfig, "maxMessages", 500)
    raw = service.store.collection.find_one({"_id": 5})
    assert raw is not None
    assert raw["features"]["summarize"] == {"maxMessages": 500}


def testUnsetRemovesStoredDefaultFields(service: GuildSettingsService) -> None:
    """Resetting a field removes it from stored feature settings."""
    service.setFeatureField(9, SummarizeConfig, "maxMessages", 500)
    service.unsetFeatureField(9, SummarizeConfig, "maxMessages")
    raw = service.store.collection.find_one({"_id": 9})
    assert raw is None or "summarize" not in raw.get("features", {})


def testResetFeatureSettingRestoresDefault(service: GuildSettingsService) -> None:
    """Resetting a feature setting restores the model default."""
    service.setFeatureField(4, SummarizeConfig, "cooldownSeconds", 120)
    assert service.getFeature(4, SummarizeConfig).cooldownSeconds == 120

    service.unsetFeatureField(4, SummarizeConfig, "cooldownSeconds")
    assert service.getFeature(4, SummarizeConfig).cooldownSeconds == COOLDOWN_SECONDS


def testNestedFeatureSettingPreservesSiblings(service: GuildSettingsService) -> None:
    """Feature updates preserve sibling fields."""
    service.setFeatureField(6, SummarizeConfig, "cooldownSeconds", 120)
    service.setFeatureField(6, SummarizeConfig, "cloudflareBaseUrl", "https://example.com")
    config = service.getFeature(6, SummarizeConfig)
    assert config.cooldownSeconds == 120
    assert config.cloudflareBaseUrl == "https://example.com"
    assert config.maxMessages == MAX_MESSAGES


def testGeneralAndFeatureSectionsAreIndependent(service: GuildSettingsService) -> None:
    """Updating general settings does not wipe feature sections."""
    service.setFeatureField(7, SummarizeConfig, "cooldownSeconds", 120)
    service.setFeatureField(7, GeneralConfig, "prefix", "!")
    assert service.getFeature(7, SummarizeConfig).cooldownSeconds == 120
    assert service.getFeature(7, GeneralConfig).prefix == "!"


def testPartialDocumentUsesModelDefaults() -> None:
    """Pydantic fills missing fields when loading a partial stored document."""
    config = SummarizeConfig.model_validate({"cooldownSeconds": 120})
    assert config.cooldownSeconds == 120
    assert config.maxMessages == MAX_MESSAGES


def testFeatureDiscovery() -> None:
    """Feature configs self-register from cogs/*/config.py."""
    features = getFeatures()
    assert "general" in features
    assert "admin" in features
    assert "summarize" in features
    assert "translations" in features
    assert features["summarize"].description


def testSettingRegistration() -> None:
    """Configurable fields register from the feature model."""
    fields = list(SummarizeConfig.model_fields)
    assert "enabled" in fields
    assert "cooldownSeconds" in fields
    assert "cloudflareBaseUrl" in fields
    assert SummarizeConfig.parseSetting("cooldownSeconds", "3600") == 3600


def testSettingDefaults() -> None:
    """Unset settings use model field defaults."""
    from pibot.cogs.summarize.config import DEFAULT_MODEL

    config = SummarizeConfig()
    assert config.cooldownSeconds == COOLDOWN_SECONDS
    assert config.maxMessages == MAX_MESSAGES
    assert config.cloudflareBaseUrl == ""
    assert config.cloudflareModel == DEFAULT_MODEL
    assert config.configured is False


def testSecretStrMasksDisplay() -> None:
    """SecretStr values are masked for display."""
    assert str(SecretStr("abcd")) == "**********"


def testGeneralConfigTypedAccess(service: GuildSettingsService) -> None:
    """GeneralConfig exposes typed attribute access."""
    config = service.getFeature(1, GeneralConfig)
    assert config.prefix == DEFAULT_PREFIX
    assert GeneralConfig.model_validate({}).prefix == DEFAULT_PREFIX
