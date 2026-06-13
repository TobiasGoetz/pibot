"""Decorators for per-guild feature gating."""

import functools
from collections.abc import Callable
from typing import Any, cast

import discord
from discord.ext import commands

from pibot.bot import Bot
from pibot.errors import FeatureDisabled, FeatureNotConfigured


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
            config = bot.guildSettings.get(interaction.guild.id)
            featureConfig = config.features.feature(featureName)
            if featureConfig is None:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"Unknown feature `{featureName}`.", ephemeral=True)
                return

            if not featureConfig.enabled:
                raise FeatureDisabled(featureName)
            if not featureConfig.configured:
                raise FeatureNotConfigured(featureName)
            return await func(cog, interaction, *args, **kwargs)

        return wrapper

    return decorator
