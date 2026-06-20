"""Translations feature settings."""

from pibot.guild_settings.model import FeatureSettings


class TranslationsConfig(FeatureSettings):
    """Translations feature settings."""

    name = "translations"
    description = "Flag-reaction translations via DeepL"
