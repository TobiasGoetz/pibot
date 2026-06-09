"""Translations feature cog package."""

from pibot.bot import Bot
from pibot.cogs.translations.cog import Translations


async def setup(bot: Bot) -> None:
    """Load translation commands."""
    await bot.add_cog(Translations(bot))
