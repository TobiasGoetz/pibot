"""Summarize feature cog package."""

from pibot.bot import Bot
from pibot.cogs.summarize.cog import Summarize


async def setup(bot: Bot) -> None:
    """Load summarize commands."""
    await bot.add_cog(Summarize(bot))
