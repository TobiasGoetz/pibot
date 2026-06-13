"""Per-guild configuration — typed root for all settings sections."""

from pydantic import Field

from pibot.cogs.summarize.config import SummarizeConfig
from pibot.cogs.translations.config import TranslationsConfig
from pibot.guild_settings.general import GeneralConfig
from pibot.guild_settings.model import FeatureSettings, SettingsGroup


class FeaturesConfig(SettingsGroup):
    """All registered feature settings for a guild."""

    summarize: SummarizeConfig = Field(default_factory=SummarizeConfig)
    translations: TranslationsConfig = Field(default_factory=TranslationsConfig)

    def feature(self, name: str) -> FeatureSettings | None:
        """Return a feature config by name, if defined on this model."""
        value = getattr(self, name, None)
        return value if isinstance(value, FeatureSettings) else None


class GuildConfig(SettingsGroup):
    """Settings for one guild."""

    general: GeneralConfig = Field(default_factory=GeneralConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
