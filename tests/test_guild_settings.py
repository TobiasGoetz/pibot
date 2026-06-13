"""Tests for per-guild settings."""

import copy

import pytest

from pibot.cogs.summarize.config import COOLDOWN_SECONDS, MAX_MESSAGES, SummarizeConfig
from pibot.cogs.translations.config import TranslationsConfig  # noqa: F401 — registers feature
from pibot.guild_settings.model import getFeatures, getSettings, readDictPath, resolveSettingKey
from pibot.guild_settings.general import DEFAULT_PREFIX
from pibot.guild_settings.service import GuildSettingsService
from pibot.guild_settings.store import SettingsStore
from pydantic import SecretStr

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

    def delete_one(self, query: dict) -> None:
        self.docs.pop(query["_id"], None)


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


class FakeSettingsStore(SettingsStore):
    """Settings store backed by in-memory collections."""

    def __init__(self) -> None:
        self.collection = FakeCollection()


@pytest.fixture(autouse=True)
def clearFeatureEnv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep feature env defaults out of tests unless explicitly set."""
    for name in (
        "DEEPL_API_KEY",
        "CLOUDFLARE_AI_URL",
        "CLOUDFLARE_AI_GATEWAY_TOKEN",
        "CLOUDFLARE_AI_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def service() -> GuildSettingsService:
    """Guild settings service with a fake store."""
    return GuildSettingsService(FakeSettingsStore())


def testDefaultsWithoutDocument(service: GuildSettingsService) -> None:
    """With no Mongo document, settings resolve from code defaults."""
    assert service.getDocument(1) == {}
    assert service.store.findById(1) is None
    assert service.general(1).prefix == DEFAULT_PREFIX
    assert service.resolve(1, SummarizeConfig).enabled is True


def testFeatureEnabledOptOut(service: GuildSettingsService) -> None:
    """Features are enabled by default and can be turned off."""
    assert service.resolve(2, SummarizeConfig).enabled is True
    service.setFeatureSetting(2, SummarizeConfig, "enabled", False)
    assert service.resolve(2, SummarizeConfig).enabled is False
    stored = service.store.findById(2)
    assert stored is not None
    assert stored["features"]["summarize"]["enabled"] is False

    service.unsetFeatureSetting(2, SummarizeConfig, "enabled")
    assert service.resolve(2, SummarizeConfig).enabled is True
    stored = service.store.findById(2)
    assert stored is not None
    assert "features" not in stored or "enabled" not in stored.get("features", {}).get("summarize", {})


def testSetAndResetPrefix(service: GuildSettingsService) -> None:
    """Guild prefix overrides persist and reset."""
    service.setPath(3, "general.prefix", "!")
    assert service.general(3).prefix == "!"
    stored = service.store.findById(3)
    assert stored is not None
    assert stored["general"]["prefix"] == "!"

    service.unsetPath(3, "general.prefix")
    assert service.general(3).prefix == DEFAULT_PREFIX
    stored = service.store.findById(3)
    assert stored is not None
    assert "general" not in stored or "prefix" not in stored.get("general", {})


def testResetFeatureSettingUnsetsOverride(service: GuildSettingsService) -> None:
    """Resetting a feature setting removes the stored override."""
    resolved = resolveSettingKey("summarize.cooldownSeconds")
    assert resolved is not None
    featureConfig, path = resolved
    service.setFeatureSetting(4, featureConfig, path, 120)
    assert service.resolve(4, SummarizeConfig).cooldownSeconds == 120

    service.unsetFeatureSetting(4, featureConfig, path)
    assert service.resolve(4, SummarizeConfig).cooldownSeconds == COOLDOWN_SECONDS
    stored = service.store.findById(4)
    assert stored is not None
    assert readDictPath(stored, "features.summarize.cooldownSeconds") is None


def testFeatureDiscovery() -> None:
    """Feature configs self-register from cogs/*/config.py."""
    features = getFeatures()
    assert "summarize" in features
    assert "translations" in features
    assert features["summarize"].description


def testSettingRegistration() -> None:
    """Configurable fields register from the feature model."""
    paths = [path for path, _ in getSettings(SummarizeConfig)]
    assert "enabled" in paths
    assert "cooldownSeconds" in paths
    assert resolveSettingKey("summarize.enabled") is not None
    resolved = resolveSettingKey("summarize.cooldownSeconds")
    assert resolved is not None
    featureConfig, path = resolved
    assert featureConfig.parseSetting(path, "3600") == 3600


def testSettingDefaultsViaResolve() -> None:
    """Unset settings resolve from model field defaults."""
    from pibot.cogs.summarize.config import DEFAULT_MODEL

    config = SummarizeConfig.resolve({})
    assert config.cooldownSeconds == COOLDOWN_SECONDS
    assert config.maxMessages == MAX_MESSAGES
    assert config.cloudflare.baseUrl == ""
    assert config.cloudflare.model == DEFAULT_MODEL
    assert config.configured is False


def testResolveFromStoredOverride() -> None:
    """Stored overrides take precedence over model defaults."""
    document = {"features": {"summarize": {"cooldownSeconds": 120}}}
    config = SummarizeConfig.resolve(document)
    assert config.cooldownSeconds == 120
    assert config.maxMessages == MAX_MESSAGES


def testSecretStrMasksDisplay() -> None:
    """SecretStr values are masked for display."""
    assert str(SecretStr("abcd")) == "**********"


def testEnvDefaultsForDeepl(monkeypatch: pytest.MonkeyPatch) -> None:
    """DEEPL_API_KEY applies when no guild override is stored."""
    monkeypatch.setenv("DEEPL_API_KEY", "env-key")
    config = TranslationsConfig.resolve({})
    assert config.deeplApiKey is not None
    assert config.deeplApiKey.get_secret_value() == "env-key"
    assert config.configured is True


def testGuildOverrideTakesPrecedenceOverEnv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stored guild settings override env defaults."""
    monkeypatch.setenv("DEEPL_API_KEY", "env-key")
    document = {"features": {"translations": {"deeplApiKey": "guild-key"}}}
    config = TranslationsConfig.resolve(document)
    assert config.deeplApiKey is not None
    assert config.deeplApiKey.get_secret_value() == "guild-key"


def testEnvDefaultsForCloudflare(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cloudflare env vars apply when no guild override is stored."""
    monkeypatch.setenv(
        "CLOUDFLARE_AI_URL",
        "https://gateway.ai.cloudflare.com/v1/acct/gw/compat",
    )
    monkeypatch.setenv("CLOUDFLARE_AI_GATEWAY_TOKEN", "token")
    monkeypatch.setenv("CLOUDFLARE_AI_MODEL", "openai/gpt-4o")
    config = SummarizeConfig.resolve({})
    assert config.cloudflare.baseUrl == "https://gateway.ai.cloudflare.com/v1/acct/gw/compat"
    assert config.cloudflare.token.get_secret_value() == "token"
    assert config.cloudflare.model == "openai/gpt-4o"
    assert config.configured is True


def testPartialCloudflareEnvOnlyAppliesSetVars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unset env vars are omitted; partial config leaves configured false."""
    monkeypatch.setenv("CLOUDFLARE_AI_URL", "https://gateway.ai.cloudflare.com/v1/acct/gw/compat")
    config = SummarizeConfig.resolve({})
    assert config.cloudflare.baseUrl == "https://gateway.ai.cloudflare.com/v1/acct/gw/compat"
    assert config.configured is False
