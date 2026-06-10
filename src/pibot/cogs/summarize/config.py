"""Summarize feature settings."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from pibot.guild_settings.model import FeatureSettings

COOLDOWN_SECONDS = 60 * 60
MAX_DURATION_SECONDS = 7 * 24 * 60 * 60
MAX_MESSAGES = 1000
DEFAULT_MODEL = "openai/gpt-4o-mini"


class CloudflareConfig(BaseModel):
    """Cloudflare AI Gateway credentials for this server."""

    model_config = ConfigDict(frozen=True)

    accountId: Annotated[str, Field(description="Cloudflare account ID for this server")] = ""
    gateway: Annotated[str, Field(description="Cloudflare AI Gateway name for this server")] = ""
    token: Annotated[SecretStr, Field(description="Cloudflare AI Gateway token for this server")] = SecretStr("")
    model: Annotated[str, Field(description="Cloudflare AI model for this server")] = DEFAULT_MODEL

    @property
    def isConfigured(self) -> bool:
        """Whether all required credentials are present."""
        return bool(self.accountId and self.gateway and self.token)


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
    def isAvailable(self) -> bool:
        """Whether summarize can run for this guild."""
        return self.enabled and self.cloudflare.isConfigured
