"""Summarize feature cog package."""

from pibot.cogs.summarize import config as _config  # noqa: F401 — registers SummarizeConfig


async def setup(bot) -> None:
    """Load summarize commands."""
    from pibot.cogs.summarize.cog import Summarize

    await bot.add_cog(Summarize(bot))
