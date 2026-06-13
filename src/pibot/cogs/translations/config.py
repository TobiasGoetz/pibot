"""Translations feature settings."""

from typing import Annotated

from pydantic import Field, SecretStr

from pibot.guild_settings.env import EnvVar
from pibot.guild_settings.model import FeatureSettings


class TranslationsConfig(FeatureSettings):
    """Translations feature settings."""

    name = "translations"
    description = "Flag-reaction translations via DeepL"

    deeplApiKey: Annotated[
        SecretStr | None,
        Field(description="DeepL API key for this server"),
        EnvVar("DEEPL_API_KEY"),
    ] = None

    @property
    def isAvailable(self) -> bool:
        """Whether translations can run for this guild."""
        return self.enabled and bool(self.deeplApiKey)
