"""
Handles errors in the bot
"""

import logging

import discord
import pibot
from discord import app_commands
from discord.ext import commands

LOGGER: logging.Logger = logging.getLogger("errors")


class ExceptionHandler(commands.Cog):
    """Error handler"""

    def __init__(self, bot: pibot.PiBot) -> None:
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
        cog: commands.Cog = interaction.command.binding
        if cog is not None:
            LOGGER.info("Cog is not None")
            if cog.has_app_command_error_handler():
                LOGGER.info("Cog has an app command error handler")
                return

        self.bot.dispatch("app_command_error", interaction, error)

    @commands.Cog.listener("on_app_command_error")
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        """
        Handles app command errors.
        :param interaction: The interaction of the slash command.
        :param error: The error that occurred.
        """

        if isinstance(error, app_commands.MissingPermissions):
            LOGGER.info(
                "User %s tried to use %s without permissions.",
                interaction.user,
                interaction.command.name,
            )
            await send_error_message(interaction, f"You cannot use `{interaction.command.name}`.", error)

        elif isinstance(error, app_commands.MissingRole):
            LOGGER.info(
                "User %s tried to use %s without the %s role.",
                interaction.user,
                interaction.command.name,
                error.missing_role,
            )
            await send_error_message(
                interaction,
                f"You cannot use `{interaction.command.name}` " f"without the {error.missing_role} role.",
                error,
            )

        elif isinstance(error, app_commands.CommandNotFound):
            LOGGER.info("User %s tried to use an invalid command.", interaction.user)
            await send_error_message(
                interaction,
                f"**{interaction.user.name}** this command does not exist.",
                error,
            )

        elif isinstance(error, app_commands.CommandSignatureMismatch):
            LOGGER.info(
                "User %s tried to use %s with invalid arguments. [%s]",
                interaction.user,
                interaction.command.name,
                error,
            )
            await send_error_message(
                interaction,
                f"You cannot use `{interaction.command.name}` " f"with those arguments.\n```{error}```",
                error,
            )

        elif isinstance(error, app_commands.CommandOnCooldown):
            LOGGER.info(
                "User %s tried to use %s on cooldown. [%s]",
                interaction.user,
                interaction.command.name,
                error,
            )
            await send_error_message(
                interaction,
                f"You cannot use `{interaction.command.name}` " f"on cooldown.\n```{error}```",
                error,
            )

        else:
            LOGGER.error(
                "Uncaught error caused by %s using %s. [%s]",
                interaction.user,
                interaction.data,
                error,
            )
            await send_error_message(
                interaction,
                f"An error occurred while using `{interaction.command.name}`.",
                error,
            )


async def send_error_message(
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

    if str(error) != "":
        embed.add_field(name="Error", value=f"```{error}```")

    try:
        await interaction.response.defer()
    except discord.errors.InteractionResponded:
        await interaction.edit_original_response(content=None, embed=embed)
    else:
        await interaction.followup.send(embed=embed)


async def setup(bot: pibot.PiBot) -> None:
    """Load the cog."""
    await bot.add_cog(ExceptionHandler(bot))
