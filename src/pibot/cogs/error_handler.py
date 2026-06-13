"""Handles errors in the bot."""

import logging

import discord
from pibot.bot import Bot
from pibot.errors import FeatureDisabled, FeatureNotConfigured
from discord import app_commands
from discord.ext import commands

LOGGER: logging.Logger = logging.getLogger("errors")


class ExceptionHandler(commands.Cog):
    """Error handler."""

    def __init__(self, bot: Bot) -> None:
        """Initialize the cog."""
        self.bot = bot
        bot.tree.error(coro=self.__dispatch_to_app_command_handler)

    async def __dispatch_to_app_command_handler(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ):
        # Avoid dispatching to the app command error handler if the command has its own error handler.
        # if hasattr(interaction.command, 'on_error'):
        #     LOGGER.info("Command has an on_error method")
        #     return

        # Avoid dispatching to the app command error handler if the cog has its own error handler.
        cog = getattr(interaction.command, "binding", None) if interaction.command else None
        if cog is not None and cog.has_app_command_error_handler():
            return

        self.bot.dispatch("app_command_error", interaction, error)

    @commands.Cog.listener("on_app_command_error")
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        """
        Handle app command errors.

        :param interaction: The interaction of the slash command.
        :param error: The error that occurred.
        """
        commandName = interaction.command.name if interaction.command else "unknown"
        if isinstance(error, app_commands.MissingPermissions):
            LOGGER.info(
                "User %s tried to use %s without permissions.",
                interaction.user,
                commandName,
            )
            await send_app_command_error_message(interaction, f"You cannot use `{commandName}`.", error)

        elif isinstance(error, app_commands.MissingRole):
            LOGGER.info(
                "User %s tried to use %s without the %s role.",
                interaction.user,
                commandName,
                error.missing_role,
            )
            await send_app_command_error_message(
                interaction,
                f"You cannot use `{commandName}` without the {error.missing_role} role.",
                error,
            )

        elif isinstance(error, app_commands.CommandNotFound):
            LOGGER.info("User %s tried to use an invalid command.", interaction.user)
            await send_app_command_error_message(
                interaction,
                f"**{interaction.user.name}** this command does not exist.",
                error,
            )

        elif isinstance(error, app_commands.CommandSignatureMismatch):
            LOGGER.info(
                "User %s tried to use %s with invalid arguments. [%s]",
                interaction.user,
                commandName,
                error,
            )
            await send_app_command_error_message(
                interaction,
                f"You cannot use `{commandName}` with those arguments.\n```{error}```",
                error,
            )

        elif isinstance(error, app_commands.CommandOnCooldown):
            LOGGER.info(
                "User %s tried to use %s on cooldown. [%s]",
                interaction.user,
                commandName,
                error,
            )
            await send_app_command_error_message(
                interaction,
                f"You cannot use `{commandName}` on cooldown.\n```{error}```",
                error,
            )

        elif isinstance(error, app_commands.CheckFailure):
            LOGGER.info(
                "User %s failed check for slash command %s.",
                interaction.user,
                commandName,
            )
            await send_app_command_error_message(interaction, f"You cannot use `{commandName}`.", error)

        elif isinstance(error, FeatureDisabled):
            LOGGER.info(
                "User %s tried to use %s while feature %s is disabled.",
                interaction.user,
                commandName,
                error.featureName,
            )
            await send_app_command_error_message(interaction, str(error), error)

        elif isinstance(error, FeatureNotConfigured):
            LOGGER.info(
                "User %s tried to use %s while feature %s is not configured.",
                interaction.user,
                commandName,
                error.featureName,
            )
            await send_app_command_error_message(interaction, str(error), error)

        else:
            LOGGER.error(
                "Uncaught error caused by %s using %s. [%s]",
                interaction.user,
                interaction.data,
                error,
            )
            await send_app_command_error_message(
                interaction,
                f"An error occurred while using `{commandName}`.",
                error,
            )

    @commands.Cog.listener("on_command_error")
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Handle prefix command errors."""
        if ctx.command and ctx.command.has_error_handler():
            return

        cog = ctx.cog
        if cog and cog.has_error_handler():
            return

        commandName = ctx.command.qualified_name if ctx.command else "unknown"
        originalError = getattr(error, "original", error)

        if isinstance(originalError, commands.CheckFailure):
            LOGGER.info(
                "User %s failed check for prefix command %s.",
                ctx.author,
                commandName,
            )
            await send_command_error_message(
                ctx,
                f"You cannot use `{commandName}`.",
                originalError,
            )
        elif isinstance(originalError, commands.MissingRequiredArgument):
            LOGGER.info(
                "User %s used %s with missing arguments. [%s]",
                ctx.author,
                commandName,
                originalError,
            )
            await send_command_error_message(
                ctx,
                f"You cannot use `{commandName}` with missing arguments.\n```{originalError}```",
                originalError,
            )
        elif isinstance(originalError, commands.BadArgument):
            LOGGER.info(
                "User %s used %s with invalid arguments. [%s]",
                ctx.author,
                commandName,
                originalError,
            )
            await send_command_error_message(
                ctx,
                f"You cannot use `{commandName}` with those arguments.\n```{originalError}```",
                originalError,
            )
        elif isinstance(originalError, commands.CommandOnCooldown):
            LOGGER.info(
                "User %s used %s on cooldown. [%s]",
                ctx.author,
                commandName,
                originalError,
            )
            await send_command_error_message(
                ctx,
                f"You cannot use `{commandName}` on cooldown.\n```{originalError}```",
                originalError,
            )
        else:
            LOGGER.error(
                "Uncaught prefix command error caused by %s using %s. [%s]",
                ctx.author,
                commandName,
                originalError,
                exc_info=originalError,
            )
            await send_command_error_message(
                ctx,
                f"An error occurred while using `{commandName}`.",
                originalError,
            )


async def send_app_command_error_message(
    interaction: discord.Interaction,
    description: str,
    error: app_commands.AppCommandError,
):
    """Send a final error message."""
    embed = discord.Embed(
        title=error.__class__.__name__,
        description=f":no_entry_sign: **{interaction.user.mention}**",
    )

    embed.add_field(name="Description", value=f"{description}")

    if str(error) != "" and str(error) != description:
        embed.add_field(name="Error", value=f"```{error}```")

    try:
        await interaction.response.defer()
    except discord.errors.InteractionResponded:
        await interaction.edit_original_response(content=None, embed=embed)
    else:
        await interaction.followup.send(embed=embed)


async def send_command_error_message(
    ctx: commands.Context,
    description: str,
    error: commands.CommandError,
):
    """Send a final prefix command error message."""
    embed = discord.Embed(
        title=error.__class__.__name__,
        description=f":no_entry_sign: **{ctx.author.mention}**",
    )

    embed.add_field(name="Description", value=f"{description}")

    if str(error) != "" and str(error) != description:
        embed.add_field(name="Error", value=f"```{error}```")

    await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    """Load the cog."""
    await bot.add_cog(ExceptionHandler(bot))
