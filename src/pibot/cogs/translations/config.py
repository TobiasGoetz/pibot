"""Translations feature settings."""

from pydantic import Field, SecretStr

from pibot.guild_settings.model import FeatureSettings


class TranslationsConfig(FeatureSettings):
    """Translations feature settings."""

    name = "translations"
    description = "Flag-reaction translations via DeepL"

    deeplApiKey: SecretStr | None = Field(
        default=None,
        description="DeepL API key for this server",
    )

    @property
    def configured(self) -> bool:
        """Whether translations is configured for this server."""
        return bool(self.deeplApiKey)
