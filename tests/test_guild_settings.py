"""Tests for per-guild settings."""

import copy

import pytest

from pibot.guild_settings.general import DEFAULT_PREFIX
from pibot.guild_settings.service import GuildSettingsService
from pibot.guild_settings.store import SettingsStore
from pibot.guild_settings.util import getNested, maskSecret


class FakeCollection:
    """In-memory MongoDB collection stub."""

    def __init__(self) -> None:
        self.docs: dict[int, dict] = {}

    def find_one(self, query: dict) -> dict | None:
        if "_id" in query:
            return copy.deepcopy(self.docs.get(query["_id"]))
        return None

    def update_one(self, query: dict, update: dict, upsert: bool = False) -> None:
        guildId = query["_id"]
        existing = self.docs.get(guildId, {"_id": guildId})
        if "$setOnInsert" in update and guildId not in self.docs:
            existing.update(copy.deepcopy(update["$setOnInsert"]))
        if "$unset" in update:
            for key in update["$unset"]:
                _unsetNested(existing, key)
        if "$set" in update:
            for key, value in update["$set"].items():
                if "." in key:
                    parts = key.split(".")
                    target = existing
                    for part in parts[:-1]:
                        target = target.setdefault(part, {})
                    target[parts[-1]] = copy.deepcopy(value)
                else:
                    existing[key] = copy.deepcopy(value)
        self.docs[guildId] = existing
        if upsert and guildId not in self.docs:
            self.docs[guildId] = existing


def _unsetNested(document: dict, dottedPath: str) -> None:
    """Remove a nested key from an in-memory document."""
    parts = dottedPath.split(".")
    target: dict = document
    for part in parts[:-1]:
        nested = target.get(part)
        if not isinstance(nested, dict):
            return
        target = nested
    if isinstance(target, dict):
        target.pop(parts[-1], None)

    def delete_one(self, query: dict) -> None:
        self.docs.pop(query["_id"], None)


class FakeSettingsStore(SettingsStore):
    """Settings store backed by in-memory collections."""

    def __init__(self) -> None:
        self.collection = FakeCollection()


@pytest.fixture
def service() -> GuildSettingsService:
    """Guild settings service with a fake store."""
    return GuildSettingsService(FakeSettingsStore())


class FakeGuild:
    """Minimal guild stand-in for ensure."""

    def __init__(self, guildId: int, name: str = "Test Guild") -> None:
        self.id = guildId
        self.name = name


@pytest.mark.asyncio
async def testEnsureGuildInsertsMetadataOnly(service: GuildSettingsService) -> None:
    """New guilds get metadata only; effective settings come from code defaults."""
    await service.ensure(FakeGuild(1))
    stored = service.store.findById(1)
    assert stored is not None
    assert stored["name"] == "Test Guild"
    assert "general" not in stored
    assert "features" not in stored

    merged = service.getDocument(1)
    assert merged == {}

    assert await service.getPrefix(1) == DEFAULT_PREFIX
    assert await service.isFeatureEnabled(1, "summarize") is True


@pytest.mark.asyncio
async def testFeatureEnabledOptOut(service: GuildSettingsService) -> None:
    """Features are enabled by default and can be turned off."""
    await service.ensure(FakeGuild(2))
    assert await service.isFeatureEnabled(2, "summarize") is True
    await service.setFeatureEnabled(2, "summarize", False)
    assert await service.isFeatureEnabled(2, "summarize") is False
    stored = service.store.findById(2)
    assert stored is not None
    assert stored["features"]["summarize"]["enabled"] is False

    await service.setFeatureEnabled(2, "summarize", True)
    assert await service.isFeatureEnabled(2, "summarize") is True
    stored = service.store.findById(2)
    assert stored is not None
    assert "features" not in stored or "enabled" not in stored.get("features", {}).get("summarize", {})


@pytest.mark.asyncio
async def testSetAndResetPrefix(service: GuildSettingsService) -> None:
    """Guild prefix overrides persist and reset."""
    await service.ensure(FakeGuild(3))
    await service.setPrefix(3, "!")
    assert await service.getPrefix(3) == "!"
    stored = service.store.findById(3)
    assert stored is not None
    assert stored["general"]["prefix"] == "!"

    await service.resetPrefix(3)
    assert await service.getPrefix(3) == DEFAULT_PREFIX
    stored = service.store.findById(3)
    assert stored is not None
    assert "general" not in stored or "prefix" not in stored.get("general", {})


@pytest.mark.asyncio
async def testResetFeatureSettingUnsetsOverride(service: GuildSettingsService) -> None:
    """Resetting a feature setting removes the stored override."""
    from pibot.cogs.summarize.config import COOLDOWN_SECONDS, SummarizeFeature

    await service.ensure(FakeGuild(4))
    path = SummarizeFeature.Cooldown.mongoPath(SummarizeFeature.name)
    service.setPath(4, path, 120)
    assert (await service.resolveFeature(4, "summarize")).cooldownSeconds == 120

    service.unsetPath(4, path)
    assert (await service.resolveFeature(4, "summarize")).cooldownSeconds == COOLDOWN_SECONDS
    stored = service.store.findById(4)
    assert stored is not None
    assert getNested(stored, ("features", "summarize", "cooldownSeconds")) is None


def testFeatureDiscovery() -> None:
    """Feature configs self-register from cogs/*/config.py."""
    from pibot.guild_settings.feature import getFeatures

    features = getFeatures()
    assert "summarize" in features
    assert "translations" in features
    assert features["summarize"].description


def testSettingRegistration() -> None:
    """Declarative settings register for autocomplete."""
    from pibot.cogs.summarize.config import SummarizeFeature
    from pibot.guild_settings.setting import getAllSettings, getSettingByKey

    getAllSettings()
    assert getSettingByKey("summarize.cooldownSeconds") is not None
    assert SummarizeFeature.Cooldown.parse("1h") == 3600


def testSettingDefaultsViaResolve() -> None:
    """Unset settings resolve from Setting.default and env fallbacks."""
    from pibot.cogs.summarize.config import COOLDOWN_SECONDS, MAX_MESSAGES, SummarizeFeature

    config = SummarizeFeature.resolve({}, enabled=True)
    assert config.cooldownSeconds == COOLDOWN_SECONDS
    assert config.maxMessages == MAX_MESSAGES
    assert config.cloudflare.accountId == ""
    assert config.cloudflare.model == "openai/gpt-4o-mini"


def testResolveFromStoredOverride() -> None:
    """Stored overrides take precedence over code defaults."""
    from pibot.cogs.summarize.config import COOLDOWN_SECONDS, SummarizeFeature

    document = {"features": {"summarize": {"cooldownSeconds": 120}}}
    config = SummarizeFeature.resolve(document, enabled=True)
    assert config.cooldownSeconds == 120
    assert config.maxMessages == SummarizeFeature.MaxMessages.default


def testMaskSecret() -> None:
    """Secrets are masked for display."""
    assert maskSecret(None) == "(not set)"
    assert maskSecret("abcd") == "****"
    assert maskSecret("abcdefghij") == "****ghij"
