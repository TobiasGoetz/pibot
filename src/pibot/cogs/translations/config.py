"""Translations feature settings."""

from pydantic import Field, SecretStr

from pibot.guild_settings.model import FeatureSettings


class TranslationsConfig(FeatureSettings):
    """Translations feature settings."""

    name = "translations"
    description = "Flag-reaction translations via DeepL"

    deeplApiKey: SecretStr = Field(
        ...,
        min_length=1,
        description="DeepL API key for this server",
    )
