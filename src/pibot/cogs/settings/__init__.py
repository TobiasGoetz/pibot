"""Settings cog package."""


async def setup(bot) -> None:
    """Load settings commands."""
    from pibot.cogs.settings.cog import Settings

    await bot.add_cog(Settings(bot))
