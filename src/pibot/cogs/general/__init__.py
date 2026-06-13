"""General feature cog package."""

from pibot.cogs.general import config as _config  # noqa: F401 — registers GeneralConfig


async def setup(bot) -> None:
    """Load general commands."""
    from pibot.cogs.general.cog import General

    await bot.add_cog(General(bot))
