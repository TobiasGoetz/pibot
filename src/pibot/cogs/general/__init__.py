"""General feature cog package."""


async def setup(bot) -> None:
    """Load general commands."""
    from pibot.cogs.general import config
    from pibot.cogs.general.cog import General

    await bot.add_cog(General(bot))
