"""Translations feature cog package."""

from pibot.cogs.translations import config as _config  # noqa: F401 — registers TranslationsConfig


async def setup(bot) -> None:
    """Load translation commands."""
    from pibot.cogs.translations.cog import Translations

    await bot.add_cog(Translations(bot))
