"""Translations feature settings."""

from dataclasses import dataclass

from pibot.guild_settings.env_defaults import deeplApiKey
from pibot.guild_settings.feature import FeatureConfig
from pibot.guild_settings.setting import Setting, SettingValueType


@dataclass(frozen=True)
class TranslationsConfig:
    """Resolved translation feature settings."""

    enabled: bool
    deeplApiKey: str | None

    @property
    def isAvailable(self) -> bool:
        """Whether translations can run for this guild."""
        return self.enabled and bool(self.deeplApiKey)


class TranslationsFeature(FeatureConfig):
    """Translations feature registration and settings resolution."""

    name = "translations"
    description = "Flag-reaction translations via DeepL"
    configClass = TranslationsConfig

    class DeeplApiKey(Setting[str]):
        """DeepL API key override for this server."""

        key = "deeplApiKey"
        description = "DeepL API key override for this server"
        valueType = SettingValueType.STRING
        secret = True
        default = None
        envDefault = deeplApiKey
