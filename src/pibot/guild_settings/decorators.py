"""Decorators for per-guild feature gating."""

import functools
from collections.abc import Callable
from typing import Any, cast

import discord
from discord.ext import commands

from pibot.bot import Bot
from pibot.errors import FeatureDisabled
from pibot.guild_settings.model import getFeature


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
            settingsClass = getFeature(featureName)
            if settingsClass is None:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"Unknown feature `{featureName}`.", ephemeral=True)
                return
            if not settingsClass.resolve(bot.guildSettings.getDocument(interaction.guild.id)).enabled:
                raise FeatureDisabled(featureName)
            return await func(cog, interaction, *args, **kwargs)

        return wrapper

    return decorator
