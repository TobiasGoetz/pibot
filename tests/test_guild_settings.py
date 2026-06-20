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

    async def find_one(self, query: dict) -> dict | None:
        """Return a stored document by ``_id``."""
        if "_id" in query:
            return copy.deepcopy(self.docs.get(query["_id"]))
        return None

    async def update_one(self, query: dict, update: dict, upsert: bool = False) -> None:
        """Apply a partial update to a stored document."""
        guildId = query["_id"]
        document = copy.deepcopy(self.docs.get(guildId, {"_id": guildId}))
        for key, value in update.get("$set", {}).items():
            self._setPath(document, key, value)
        for key in update.get("$unset", {}):
            self._unsetPath(document, key)
        self.docs[guildId] = document

    @staticmethod
    def _setPath(document: dict, key: str, value: object) -> None:
        parts = key.split(".")
        cursor: dict = document
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = copy.deepcopy(value)

    @staticmethod
    def _unsetPath(document: dict, key: str) -> None:
        parts = key.split(".")
        cursor: object = document
        for part in parts[:-1]:
            if not isinstance(cursor, dict) or part not in cursor:
                return
            cursor = cursor[part]
        if isinstance(cursor, dict):
            cursor.pop(parts[-1], None)
            if not cursor and len(parts) > 1:
                parent: dict = document
                for part in parts[:-2]:
                    parent = parent[part]
                if not parent.get(parts[-2]):
                    parent.pop(parts[-2], None)
                if not parent and len(parts) > 2 and parts[0] in document and not document[parts[0]]:
                    document.pop(parts[0], None)

    async def delete_one(self, query: dict) -> None:
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


async def testDefaultsWithoutDocument(service: GuildSettingsService) -> None:
    """With no Mongo document, settings use model defaults."""
    assert (await service.getFeature(1, GeneralConfig)).prefix == DEFAULT_PREFIX
    assert (await service.getFeature(1, SummarizeConfig)).enabled is True


async def testFeatureEnabledOptOut(service: GuildSettingsService) -> None:
    """Feature enabled flag persists via Pydantic round-trip."""
    assert (await service.getFeature(2, SummarizeConfig)).enabled is True
    await service.setFeatureField(2, SummarizeConfig, "enabled", False)
    assert (await service.getFeature(2, SummarizeConfig)).enabled is False
    stored = await service.store.findFeature(2, SummarizeConfig.name, SummarizeConfig)
    assert stored.enabled is False

    await service.unsetFeatureField(2, SummarizeConfig, "enabled")
    assert (await service.getFeature(2, SummarizeConfig)).enabled is True


async def testSetAndResetPrefix(service: GuildSettingsService) -> None:
    """Guild prefix persists and resets to the model default."""
    await service.setFeatureField(3, GeneralConfig, "prefix", "!")
    assert (await service.getFeature(3, GeneralConfig)).prefix == "!"
    stored = await service.store.findFeature(3, GeneralConfig.name, GeneralConfig)
    assert stored.prefix == "!"

    await service.unsetFeatureField(3, GeneralConfig, "prefix")
    assert (await service.getFeature(3, GeneralConfig)).prefix == DEFAULT_PREFIX


async def testSparseStorageOmitsDefaults(service: GuildSettingsService) -> None:
    """MongoDB stores only fields that differ from model defaults."""
    await service.setFeatureField(5, SummarizeConfig, "maxMessages", 500)
    raw = await service.store.collection.find_one({"_id": 5})
    assert raw is not None
    assert raw["features"]["summarize"] == {"maxMessages": 500}


async def testUnsetRemovesStoredDefaultFields(service: GuildSettingsService) -> None:
    """Resetting a field removes it from stored feature settings."""
    await service.setFeatureField(9, SummarizeConfig, "maxMessages", 500)
    await service.unsetFeatureField(9, SummarizeConfig, "maxMessages")
    raw = await service.store.collection.find_one({"_id": 9})
    assert raw is None or "summarize" not in raw.get("features", {})


async def testResetFeatureSettingRestoresDefault(service: GuildSettingsService) -> None:
    """Resetting a feature setting restores the model default."""
    await service.setFeatureField(4, SummarizeConfig, "cooldownSeconds", 120)
    assert (await service.getFeature(4, SummarizeConfig)).cooldownSeconds == 120

    await service.unsetFeatureField(4, SummarizeConfig, "cooldownSeconds")
    assert (await service.getFeature(4, SummarizeConfig)).cooldownSeconds == COOLDOWN_SECONDS


async def testNestedFeatureSettingPreservesSiblings(service: GuildSettingsService) -> None:
    """Feature updates preserve sibling fields."""
    await service.setFeatureField(6, SummarizeConfig, "cooldownSeconds", 120)
    await service.setFeatureField(6, SummarizeConfig, "cloudflareBaseUrl", "https://example.com")
    config = await service.getFeature(6, SummarizeConfig)
    assert config.cooldownSeconds == 120
    assert config.cloudflareBaseUrl == "https://example.com"
    assert config.maxMessages == MAX_MESSAGES


async def testGeneralAndFeatureSectionsAreIndependent(service: GuildSettingsService) -> None:
    """Updating general settings does not wipe feature sections."""
    await service.setFeatureField(7, SummarizeConfig, "cooldownSeconds", 120)
    await service.setFeatureField(7, GeneralConfig, "prefix", "!")
    assert (await service.getFeature(7, SummarizeConfig)).cooldownSeconds == 120
    assert (await service.getFeature(7, GeneralConfig)).prefix == "!"


def testPartialDocumentUsesModelDefaults() -> None:
    """Partial stored documents merge with optional model defaults."""
    config = SummarizeConfig.fromStored({"cooldownSeconds": 120})
    assert config.cooldownSeconds == 120
    assert config.maxMessages == MAX_MESSAGES
    assert config.configured is False


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
    """Unset required settings are absent until stored."""
    from pibot.cogs.summarize.config import DEFAULT_MODEL

    config = SummarizeConfig.fromStored({})
    assert config.cooldownSeconds == COOLDOWN_SECONDS
    assert config.maxMessages == MAX_MESSAGES
    assert config.cloudflareModel == DEFAULT_MODEL
    assert config.configured is False
    assert "cloudflareBaseUrl" not in config.model_fields_set


def testSecretStrMasksDisplay() -> None:
    """SecretStr values are masked for display."""
    assert str(SecretStr("abcd")) == "**********"


async def testSetOptionalToDefaultRemovesStoredField(service: GuildSettingsService) -> None:
    """Setting an optional field back to its default removes it from MongoDB."""
    await service.setFeatureField(11, SummarizeConfig, "maxMessages", 500)
    await service.setFeatureField(11, SummarizeConfig, "cooldownSeconds", 120)
    await service.setFeatureField(11, SummarizeConfig, "maxMessages", MAX_MESSAGES)

    raw = await service.store.collection.find_one({"_id": 11})
    assert raw is not None
    assert raw["features"]["summarize"] == {"cooldownSeconds": 120}


async def testRequiredSettingResetRemovesStoredField(service: GuildSettingsService) -> None:
    """Resetting a required setting removes it from MongoDB."""
    await service.setFeatureField(10, SummarizeConfig, "cloudflareBaseUrl", "https://example.com")
    await service.setFeatureField(10, SummarizeConfig, "cloudflareToken", SecretStr("token"))
    assert (await service.getFeature(10, SummarizeConfig)).configured is True

    await service.unsetFeatureField(10, SummarizeConfig, "cloudflareBaseUrl")
    config = await service.getFeature(10, SummarizeConfig)
    assert config.configured is False
    assert "cloudflareBaseUrl" not in config.model_fields_set
    raw = await service.store.collection.find_one({"_id": 10})
    assert raw is not None
    assert "cloudflareBaseUrl" not in raw["features"]["summarize"]


async def testGeneralConfigTypedAccess(service: GuildSettingsService) -> None:
    """GeneralConfig exposes typed attribute access."""
    config = await service.getFeature(1, GeneralConfig)
    assert config.prefix == DEFAULT_PREFIX
    assert GeneralConfig.model_validate({}).prefix == DEFAULT_PREFIX
