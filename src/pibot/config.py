"""
Bot-level configuration loaded from the environment (never persisted to MongoDB).

Environment variable convention
---------------------------------
All PiBot env vars use the ``PIBOT_`` prefix.

- **Bootstrap / runtime:** ``PIBOT_{NAME}`` — e.g. ``PIBOT_DISCORD_TOKEN``, ``PIBOT_LOG_LEVEL``
- **Feature integrations:** ``PIBOT_{FEATURE}_{VENDOR}_{FIELD}`` — e.g.
  ``PIBOT_SUMMARIZE_CLOUDFLARE_BASE_URL``, ``PIBOT_TRANSLATIONS_DEEPL_API_KEY``

Guild settings are never read from the environment (MongoDB only).
"""

import logging
from enum import StrEnum

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "PIBOT_"
SUMMARIZE_FEATURE = "SUMMARIZE"
TRANSLATIONS_FEATURE = "TRANSLATIONS"


class COMMAND_SYNC_BEHAVIOR(StrEnum):
    """Env ``PIBOT_COMMAND_SYNC_BEHAVIOR``."""

    GLOBAL = "global"
    LOCAL = "local"


class CloudflareSettings(BaseSettings):
    """Summarize feature — Cloudflare AI Gateway credentials."""

    model_config = SettingsConfigDict(
        frozen=True,
        extra="ignore",
        env_ignore_empty=True,
        env_prefix=f"{ENV_PREFIX}{SUMMARIZE_FEATURE}_CLOUDFLARE_",
        env_prefix_target="alias",
    )

    baseUrl: str | None = Field(default=None, min_length=1, alias="BASE_URL")
    token: SecretStr | None = Field(default=None, min_length=1, alias="TOKEN")

    @property
    def configured(self) -> bool:
        """Whether both base URL and token are set."""
        return self.baseUrl is not None and self.token is not None


class DeeplSettings(BaseSettings):
    """Translations feature — DeepL API credentials."""

    model_config = SettingsConfigDict(
        frozen=True,
        extra="ignore",
        env_ignore_empty=True,
        env_prefix=f"{ENV_PREFIX}{TRANSLATIONS_FEATURE}_DEEPL_",
        env_prefix_target="alias",
    )

    apiKey: SecretStr | None = Field(default=None, min_length=1, alias="API_KEY")

    @property
    def configured(self) -> bool:
        """Whether the API key is set."""
        return self.apiKey is not None


class SummarizeBotConfig(BaseSettings):
    """Summarize feature — bot-level integration settings."""

    model_config = SettingsConfigDict(frozen=True, extra="ignore")

    cloudflare: CloudflareSettings = Field(default_factory=CloudflareSettings)


class TranslationsBotConfig(BaseSettings):
    """Translations feature — bot-level integration settings."""

    model_config = SettingsConfigDict(frozen=True, extra="ignore")

    deepl: DeeplSettings = Field(default_factory=DeeplSettings)


class BotConfig(BaseSettings):
    """Runtime bot configuration from environment variables."""

    model_config = SettingsConfigDict(
        frozen=True,
        extra="ignore",
        env_ignore_empty=True,
        env_prefix=ENV_PREFIX,
        env_prefix_target="alias",
    )

    discordToken: str = Field(min_length=1, alias="DISCORD_TOKEN")
    mongodbUri: str = Field(min_length=1, alias="MONGODB_URI")
    logLevel: str = Field(default="INFO", alias="LOG_LEVEL")
    summarize: SummarizeBotConfig = Field(default_factory=SummarizeBotConfig)
    translations: TranslationsBotConfig = Field(default_factory=TranslationsBotConfig)
    commandSyncBehavior: COMMAND_SYNC_BEHAVIOR = Field(
        default=COMMAND_SYNC_BEHAVIOR.GLOBAL,
        alias="COMMAND_SYNC_BEHAVIOR",
    )
    enableDevTools: bool = Field(default=False, alias="ENABLE_DEV_TOOLS")

    @property
    def logLevelValue(self) -> int:
        """``PIBOT_LOG_LEVEL`` as a ``logging`` module level constant."""
        return getattr(logging, self.logLevel.upper(), logging.INFO)
