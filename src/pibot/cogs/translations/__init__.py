"""Translations feature cog package."""


async def setup(bot) -> None:
    """Load translation commands."""
    from pibot.cogs.translations import config
    from pibot.cogs.translations.cog import Translations

    await bot.add_cog(Translations(bot))
