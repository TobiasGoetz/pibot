"""Summarize feature settings."""

from pydantic import Field

from pibot.guild_settings.model import SettingsGroup


class SummarizeConfig(SettingsGroup):
    """Summarize feature settings."""

    name = "summarize"
    description = "AI channel summaries via Cloudflare"

    cooldownSeconds: int = Field(
        default=60 * 60,
        description="Cooldown between /summarize channel uses (seconds)",
    )
    maxDurationSeconds: int = Field(
        default=7 * 24 * 60 * 60,
        description="Maximum lookback duration for /summarize channel (seconds)",
    )
    maxMessages: int = Field(
        default=1000,
        description="Maximum messages per summary",
    )
    cloudflareModel: str = Field(
        default="openai/gpt-4o-mini",
        description="Cloudflare AI model for this server",
    )
