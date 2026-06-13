"""Summarize feature settings."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from pibot.guild_settings.env import EnvVar
from pibot.guild_settings.model import FeatureSettings

COOLDOWN_SECONDS = 60 * 60
MAX_DURATION_SECONDS = 7 * 24 * 60 * 60
MAX_MESSAGES = 1000
DEFAULT_MODEL = "openai/gpt-4o-mini"


class CloudflareConfig(BaseModel):
    """Cloudflare AI Gateway credentials for this server."""

    model_config = ConfigDict(frozen=True)

    baseUrl: Annotated[
        str,
        Field(description="Cloudflare AI Gateway base URL (through `/compat`; the client appends `/chat/completions`)"),
        EnvVar("CLOUDFLARE_AI_URL"),
    ] = ""
    token: Annotated[
        SecretStr,
        Field(description="Cloudflare AI Gateway token for this server"),
        EnvVar("CLOUDFLARE_AI_GATEWAY_TOKEN"),
    ] = SecretStr("")
    model: Annotated[
        str,
        Field(description="Cloudflare AI model for this server"),
        EnvVar("CLOUDFLARE_AI_MODEL"),
    ] = DEFAULT_MODEL

    @property
    def isConfigured(self) -> bool:
        """Whether all required credentials are present."""
        return bool(self.baseUrl and self.token.get_secret_value())


class SummarizeConfig(FeatureSettings):
    """Summarize feature settings."""

    name = "summarize"
    description = "AI channel summaries via Cloudflare"

    cooldownSeconds: Annotated[int, Field(description="Cooldown between /summarize uses (seconds)")] = COOLDOWN_SECONDS
    maxDurationSeconds: Annotated[
        int,
        Field(description="Maximum lookback duration for /summarize (seconds)"),
    ] = MAX_DURATION_SECONDS
    maxMessages: Annotated[int, Field(description="Maximum messages per summary")] = MAX_MESSAGES
    cloudflare: CloudflareConfig = Field(default_factory=CloudflareConfig)

    @property
    def configured(self) -> bool:
        """Whether summarize is configured for this guild."""
        return self.cloudflare.isConfigured
