"""Tests for bot-level configuration loaded from env."""

import pytest
from pydantic import ValidationError

from pibot.config import BotConfig, COMMAND_SYNC_BEHAVIOR


@pytest.fixture(autouse=True)
def clearBotEnv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure bot env vars do not leak between tests."""
    for name in (
        "PIBOT_DISCORD_TOKEN",
        "PIBOT_MONGODB_URI",
        "PIBOT_SUMMARIZE_CLOUDFLARE_BASE_URL",
        "PIBOT_SUMMARIZE_CLOUDFLARE_TOKEN",
        "PIBOT_TRANSLATIONS_DEEPL_API_KEY",
        "PIBOT_COMMAND_SYNC_BEHAVIOR",
        "PIBOT_ENABLE_DEV_TOOLS",
        "PIBOT_LOG_LEVEL",
    ):
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setenv("PIBOT_DISCORD_TOKEN", "discord-token")
    monkeypatch.setenv("PIBOT_MONGODB_URI", "mongodb://localhost:27017/")


def testCloudflareConfiguredRequiresBothValues(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cloudflare is configured only when base URL and token are set."""
    config = BotConfig()
    assert config.summarize.cloudflare.configured is False

    monkeypatch.setenv("PIBOT_SUMMARIZE_CLOUDFLARE_BASE_URL", "https://example.com")
    assert BotConfig().summarize.cloudflare.configured is False

    monkeypatch.setenv("PIBOT_SUMMARIZE_CLOUDFLARE_TOKEN", "token")
    config = BotConfig()
    assert config.summarize.cloudflare.configured is True
    assert config.summarize.cloudflare.baseUrl == "https://example.com"
    assert config.summarize.cloudflare.token is not None
    assert config.summarize.cloudflare.token.get_secret_value() == "token"


def testDeeplConfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepL is configured when the API key env var is set."""
    assert BotConfig().translations.deepl.configured is False

    monkeypatch.setenv("PIBOT_TRANSLATIONS_DEEPL_API_KEY", "key")
    config = BotConfig()
    assert config.translations.deepl.configured is True
    assert config.translations.deepl.apiKey is not None
    assert config.translations.deepl.apiKey.get_secret_value() == "key"


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
