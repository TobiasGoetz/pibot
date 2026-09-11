"""Userstats feature cog package."""


async def setup(bot) -> None:
    """Load userstats commands."""
    from pibot.cogs.userstats import config
    from pibot.cogs.userstats.cog import Userstats

    cog = Userstats(bot)
    await cog.store.ensureIndexes()
    await bot.add_cog(cog)
