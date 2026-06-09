"""Decorators for per-guild feature gating."""

import functools
from collections.abc import Callable
from typing import Any, cast

import discord
from discord.ext import commands

from pibot.bot import Bot
from pibot.guild_settings.feature import getFeature

FEATURE_DISABLED_MESSAGE = (
    "This feature is disabled on this server. An administrator can enable it with `/settings feature`."
)


def requiresFeature(featureName: str) -> Callable:
    """Require a feature to be enabled for the interaction guild."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(cog: commands.Cog, interaction: discord.Interaction, *args: Any, **kwargs: Any):
            if interaction.guild is None:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "This command can only be used in a server.", ephemeral=True
                    )
                return
            bot = cast(Bot, getattr(cog, "bot"))
            if getFeature(featureName) is None:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"Unknown feature `{featureName}`.", ephemeral=True)
                return
            if not await bot.guildSettings.isFeatureEnabled(interaction.guild.id, featureName):
                if not interaction.response.is_done():
                    await interaction.response.send_message(FEATURE_DISABLED_MESSAGE, ephemeral=True)
                return
            return await func(cog, interaction, *args, **kwargs)

        return wrapper

    return decorator
