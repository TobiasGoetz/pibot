"""Translations feature cog package."""

from pibot.bot import Bot
from pibot.cogs.translations import config as _config  # noqa: F401 — registers TranslationsConfig
from pibot.cogs.translations.cog import Translations


async def setup(bot: Bot) -> None:
    """Load translation commands."""
    await bot.add_cog(Translations(bot))
