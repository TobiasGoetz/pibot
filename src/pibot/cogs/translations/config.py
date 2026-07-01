"""Translations feature settings."""

from pibot.guild_settings.model import SettingsGroup


class TranslationsConfig(SettingsGroup):
    """Translations feature settings."""

    name = "translations"
    description = "Flag-reaction translations via DeepL"
