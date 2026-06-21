"""Tests for bot-level configuration loaded from env."""

import pytest
from pydantic import ValidationError

from pibot.config import BotConfig, COMMAND_SYNC_BEHAVIOR


@pytest.fixture(autouse=True)
def botEnv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset PIBOT_* env to a known baseline, ignoring host environment."""
    # Optional vars: remove so pydantic defaults apply
    for name in (
        "PIBOT_COMMAND_SYNC_BEHAVIOR",
        "PIBOT_ENABLE_DEV_TOOLS",
        "PIBOT_LOG_LEVEL",
    ):
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setenv("PIBOT_DISCORD_TOKEN", "discord-token")
    monkeypatch.setenv("PIBOT_MONGODB_URI", "mongodb://localhost:27017/")
    monkeypatch.setenv("PIBOT_SUMMARIZE_CLOUDFLARE_BASE_URL", "https://example.com")
    monkeypatch.setenv("PIBOT_SUMMARIZE_CLOUDFLARE_TOKEN", "cloudflare-token")
    monkeypatch.setenv("PIBOT_TRANSLATIONS_DEEPL_API_KEY", "deepl-key")


def testCloudflareCredentialsLoadFromEnv() -> None:
    """Cloudflare credentials load from env."""
    config = BotConfig()
    assert config.summarize.cloudflare.baseUrl == "https://example.com"
    assert config.summarize.cloudflare.token.get_secret_value() == "cloudflare-token"


def testDeeplApiKeyLoadsFromEnv() -> None:
    """DeepL API key loads from env."""
    config = BotConfig()
    assert config.translations.deepl.apiKey.get_secret_value() == "deepl-key"


def testRuntimeFlagsFromEnv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Command sync and DevTools flags load from env."""
    config = BotConfig()
    assert config.commandSyncBehavior is COMMAND_SYNC_BEHAVIOR.GLOBAL
    assert config.enableDevTools is False

    monkeypatch.setenv("PIBOT_COMMAND_SYNC_BEHAVIOR", "local")
    monkeypatch.setenv("PIBOT_ENABLE_DEV_TOOLS", "true")
    config = BotConfig()
    assert config.commandSyncBehavior is COMMAND_SYNC_BEHAVIOR.LOCAL
    assert config.enableDevTools is True


def testInvalidCommandSyncBehaviorRaises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid command sync env values fail at config load."""
    monkeypatch.setenv("PIBOT_COMMAND_SYNC_BEHAVIOR", "nope")
    with pytest.raises(ValidationError):
        BotConfig()


def testRequiredBootstrapVarsRaiseWhenMissing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bootstrap env vars are required."""
    monkeypatch.delenv("PIBOT_DISCORD_TOKEN", raising=False)
    with pytest.raises(ValidationError):
        BotConfig()


def testRequiredCloudflareVarsRaiseWhenMissing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cloudflare env vars are required."""
    monkeypatch.delenv("PIBOT_SUMMARIZE_CLOUDFLARE_BASE_URL", raising=False)
    with pytest.raises(ValidationError):
        BotConfig()

    monkeypatch.setenv("PIBOT_SUMMARIZE_CLOUDFLARE_BASE_URL", "https://example.com")
    monkeypatch.delenv("PIBOT_SUMMARIZE_CLOUDFLARE_TOKEN", raising=False)
    with pytest.raises(ValidationError):
        BotConfig()


def testRequiredDeeplApiKeyRaisesWhenMissing(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepL API key env var is required."""
    monkeypatch.delenv("PIBOT_TRANSLATIONS_DEEPL_API_KEY", raising=False)
    with pytest.raises(ValidationError):
        BotConfig()
