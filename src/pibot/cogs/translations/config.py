"""Translations feature settings."""

from pibot.config import BotConfig
from pibot.guild_settings.model import FeatureSettings


class TranslationsConfig(FeatureSettings):
    """Translations feature settings."""

    name = "translations"
    description = "Flag-reaction translations via DeepL"

    @classmethod
    def isBotReady(cls, botConfig: BotConfig) -> bool:
        """Whether a bot-level DeepL API key is present."""
        return botConfig.translations.deepl.configured
