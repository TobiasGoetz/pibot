"""Translations feature settings."""

from pibot.guild_settings.model import SettingsGroup
from pibot.guild_settings.registry import registerSettingsGroup


@registerSettingsGroup
class TranslationsConfig(SettingsGroup):
    """Translations feature settings."""

    name = "translations"
    description = "Flag-reaction translations via DeepL"
