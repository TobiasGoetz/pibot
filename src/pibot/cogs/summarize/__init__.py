"""Summarize feature cog package."""


async def setup(bot) -> None:
    """Load summarize commands."""
    from pibot.cogs.summarize import config
    from pibot.cogs.summarize.cog import Summarize

    await bot.add_cog(Summarize(bot))
