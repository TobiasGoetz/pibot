"""Summarize feature settings."""

from pydantic import Field, SecretStr

from pibot.guild_settings.model import FeatureSettings

COOLDOWN_SECONDS = 60 * 60
MAX_DURATION_SECONDS = 7 * 24 * 60 * 60
MAX_MESSAGES = 1000
DEFAULT_MODEL = "openai/gpt-4o-mini"


class SummarizeConfig(FeatureSettings):
    """Summarize feature settings."""

    name = "summarize"
    description = "AI channel summaries via Cloudflare"

    cooldownSeconds: int = Field(
        default=COOLDOWN_SECONDS,
        description="Cooldown between /summarize channel uses (seconds)",
    )
    maxDurationSeconds: int = Field(
        default=MAX_DURATION_SECONDS,
        description="Maximum lookback duration for /summarize channel (seconds)",
    )
    maxMessages: int = Field(
        default=MAX_MESSAGES,
        description="Maximum messages per summary",
    )
    cloudflareBaseUrl: str = Field(
        ...,
        min_length=1,
        description=("Cloudflare AI Gateway base URL (through `/compat`; the client appends `/chat/completions`)"),
    )
    cloudflareToken: SecretStr = Field(
        ...,
        min_length=1,
        description="Cloudflare AI Gateway token for this server",
    )
    cloudflareModel: str = Field(
        default=DEFAULT_MODEL,
        description="Cloudflare AI model for this server",
    )
