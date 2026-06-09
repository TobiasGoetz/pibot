"""Summarize feature settings."""

from dataclasses import dataclass

from pibot.guild_settings.env_defaults import cloudflareConfig
from pibot.guild_settings.feature import FeatureConfig
from pibot.guild_settings.setting import Setting, SettingValueType

COOLDOWN_SECONDS = 60 * 60
MAX_DURATION_SECONDS = 7 * 24 * 60 * 60
MAX_MESSAGES = 1000
DEFAULT_MODEL = "openai/gpt-4o-mini"


def _envCloudflareAccountId() -> str:
    envCf = cloudflareConfig()
    return envCf.accountId if envCf else ""


def _envCloudflareGateway() -> str:
    envCf = cloudflareConfig()
    return envCf.gateway if envCf else ""


def _envCloudflareToken() -> str:
    envCf = cloudflareConfig()
    return envCf.token if envCf else ""


def _envCloudflareModel() -> str:
    envCf = cloudflareConfig()
    if envCf and envCf.model:
        return envCf.model
    return DEFAULT_MODEL


@dataclass(frozen=True)
class CloudflareConfig:
    """Resolved Cloudflare AI Gateway credentials."""

    accountId: str
    gateway: str
    token: str
    model: str

    @property
    def isConfigured(self) -> bool:
        """Whether all required credentials are present."""
        return bool(self.accountId and self.gateway and self.token)


@dataclass(frozen=True)
class SummarizeConfig:
    """Resolved summarize feature settings."""

    enabled: bool
    cooldownSeconds: int
    maxDurationSeconds: int
    maxMessages: int
    cloudflare: CloudflareConfig

    @property
    def isAvailable(self) -> bool:
        """Whether summarize can run for this guild."""
        return self.enabled and self.cloudflare.isConfigured


class SummarizeFeature(FeatureConfig):
    """Summarize feature registration and settings resolution."""

    name = "summarize"
    description = "AI channel summaries via Cloudflare"
    configClass = SummarizeConfig
    nestedConfigs = {"cloudflare": CloudflareConfig}

    class Cooldown(Setting[int]):
        """Cooldown between /summarize uses."""

        key = "cooldownSeconds"
        description = "Cooldown between /summarize uses"
        valueType = SettingValueType.DURATION
        default = COOLDOWN_SECONDS

    class MaxDuration(Setting[int]):
        """Maximum lookback duration for /summarize."""

        key = "maxDurationSeconds"
        description = "Maximum lookback duration for /summarize"
        valueType = SettingValueType.DURATION
        default = MAX_DURATION_SECONDS

    class MaxMessages(Setting[int]):
        """Maximum messages per summary."""

        key = "maxMessages"
        description = "Maximum messages per summary"
        valueType = SettingValueType.INT
        default = MAX_MESSAGES

    class CloudflareAccountId(Setting[str]):
        """Cloudflare account ID override."""

        key = "cloudflare.accountId"
        description = "Cloudflare account ID override"
        valueType = SettingValueType.STRING
        default = None
        envDefault = _envCloudflareAccountId

    class CloudflareGateway(Setting[str]):
        """Cloudflare AI Gateway name override."""

        key = "cloudflare.gateway"
        description = "Cloudflare AI Gateway name override"
        valueType = SettingValueType.STRING
        default = None
        envDefault = _envCloudflareGateway

    class CloudflareToken(Setting[str]):
        """Cloudflare AI Gateway token override."""

        key = "cloudflare.token"
        description = "Cloudflare AI Gateway token override"
        valueType = SettingValueType.STRING
        secret = True
        default = None
        envDefault = _envCloudflareToken

    class CloudflareModel(Setting[str]):
        """Cloudflare AI model override."""

        key = "cloudflare.model"
        description = "Cloudflare AI model override"
        valueType = SettingValueType.STRING
        default = None
        envDefault = _envCloudflareModel
