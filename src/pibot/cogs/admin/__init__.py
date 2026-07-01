"""Admin feature cog package."""

from pibot.cogs.admin import config as _config  # noqa: F401 — registers AdminConfig


async def setup(bot) -> None:
    """Load admin commands."""
    from pibot.cogs.admin.cog import Admin

    await bot.add_cog(Admin(bot))
