"""General cog."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import discord
import pytimeparse
from discord import app_commands
from discord.ext import commands

from pibot.bot import Bot
from pibot.cogs.general.config import GeneralConfig
from pibot.guild_settings.feature_mixin import FeatureSettingsMixin

logger = logging.getLogger("cog.general")


class General(
    FeatureSettingsMixin,
    commands.GroupCog,
    group_name="general",
    group_description="Core bot utilities and settings",
):
    """General commands."""

    featureConfig = GeneralConfig

    def __init__(self, bot: Bot) -> None:
        """Initialize the cog."""
        self.bot = bot

    @app_commands.command(name="ping", description="Displays the bots ping.")
    async def ping(self, interaction: discord.Interaction) -> None:
        """Display the bots ping."""
        await interaction.response.send_message(f"Ping: {self.bot.latency * 1000:.0f}ms", ephemeral=True)

    @app_commands.command(name="version", description="Displays the bot version.")
    async def version(self, interaction: discord.Interaction) -> None:
        """Display the bot's version."""
        await interaction.response.send_message(
            embed=discord.Embed(
                title="PiBot Version",
                description=self.bot.version,
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="countdown",
        description="Start a countdown for a specified amount of time.",
    )
    async def countdown(self, interaction: discord.Interaction, time_str: str) -> None:
        """
        Start a countdown for a specified amount of time.

        :param interaction: The interaction of the slash command.
        :param time_str: The time to count down from.
        """
        if interaction.guild is None:
            return
        config = await self.bot.guildSettings.getFeature(interaction.guild.id, GeneralConfig)
        seconds = pytimeparse.parse(time_str)

        if seconds is None:
            raise commands.BadArgument(f"Could not parse {time_str} as a time.")
        if seconds < 0:
            raise commands.BadArgument("Time cannot be negative.")
        if seconds > config.countdownMaxSeconds:
            raise commands.BadArgument(
                f"Countdowns cannot be longer than {config.countdownMaxSeconds} seconds.",
            )

        start_time = interaction.created_at
        end_time = (start_time + timedelta(seconds=seconds)).strftime("%H:%M:%S")
        logger.info("%s started a countdown for %s seconds.", interaction.user, seconds)
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"Countdown - {seconds}s",
                description=(f"{seconds} seconds remaining.\nEnds at {end_time} UTC."),
            )
        )

        while (datetime.now(UTC) - start_time).total_seconds() < seconds:
            await interaction.edit_original_response(
                embed=discord.Embed(
                    title=f"Countdown - {seconds}s",
                    description=f"{seconds - round((datetime.now(UTC) - start_time).total_seconds())}"
                    f"seconds remaining.\n"
                    f"Ends at {end_time} UTC.",
                )
            )
            await asyncio.sleep(1)

        await interaction.edit_original_response(
            embed=discord.Embed(
                title=f"Countdown - {seconds}s",
                description=f"Countdown finished at {end_time} UTC.",
            )
        )
        logger.info("Finished %s's countdown for %s seconds.", interaction.user, seconds)
