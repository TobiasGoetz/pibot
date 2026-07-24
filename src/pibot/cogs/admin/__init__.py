"""Admin feature cog package."""


async def setup(bot) -> None:
    """Load admin commands."""
    from pibot.cogs.admin import config
    from pibot.cogs.admin.cog import Admin

    await bot.add_cog(Admin(bot))
