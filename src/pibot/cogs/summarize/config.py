"""Summarize feature settings."""

from typing import Annotated, Any

from pydantic import Field, SecretStr, model_validator

from pibot.guild_settings.env import EnvVar
from pibot.guild_settings.model import FeatureSettings

COOLDOWN_SECONDS = 60 * 60
MAX_DURATION_SECONDS = 7 * 24 * 60 * 60
MAX_MESSAGES = 1000
DEFAULT_MODEL = "openai/gpt-4o-mini"


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
    cloudflareBaseUrl: Annotated[
        str,
        Field(description="Cloudflare AI Gateway base URL (through `/compat`; the client appends `/chat/completions`)"),
        EnvVar("CLOUDFLARE_AI_URL"),
    ] = ""
    cloudflareToken: Annotated[
        SecretStr,
        Field(description="Cloudflare AI Gateway token for this server"),
        EnvVar("CLOUDFLARE_AI_GATEWAY_TOKEN"),
    ] = SecretStr("")
    cloudflareModel: Annotated[
        str,
        Field(description="Cloudflare AI model for this server"),
        EnvVar("CLOUDFLARE_AI_MODEL"),
    ] = DEFAULT_MODEL

    @model_validator(mode="before")
    @classmethod
    def migrateLegacyCloudflareGroup(cls, data: Any) -> Any:
        """Map nested ``cloudflare`` documents from older stored configs."""
        if not isinstance(data, dict):
            return data
        cloudflare = data.pop("cloudflare", None)
        if not isinstance(cloudflare, dict):
            return data
        legacyFields = {
            "cloudflareBaseUrl": cloudflare.get("baseUrl", ""),
            "cloudflareToken": cloudflare.get("token", ""),
            "cloudflareModel": cloudflare.get("model", DEFAULT_MODEL),
        }
        for key, value in legacyFields.items():
            data.setdefault(key, value)
        return data

    @property
    def configured(self) -> bool:
        """Whether summarize is configured for this guild."""
        return bool(self.cloudflareBaseUrl and self.cloudflareToken.get_secret_value())
