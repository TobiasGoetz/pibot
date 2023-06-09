"""
Handles errors in the bot
"""
import logging

import discord
from discord import app_commands
from discord.ext import commands

import errors
import pibot

LOGGER: logging.Logger = logging.getLogger('errors')


class ExceptionHandler(commands.Cog):
    """ Handles errors in the bot. """

    def __init__(self, bot: pibot.PiBot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, interaction: discord.Interaction,
                               error: discord.app_commands.AppCommandError) -> None:
        """ When a command has an error. """
        if isinstance(error, app_commands.MissingPermissions):
            LOGGER.info('User %s tried to use %s without permissions.', interaction.user, interaction.command.name)
            await self.send_final_error_message(interaction, f'You cannot use `{interaction.command.name}`.', error)

        elif isinstance(error, app_commands.MissingRole):
            LOGGER.info(
                'User %s tried to use %s without the %s role.',
                interaction.user, interaction.command.name, error.missing_role
            )
            await self.send_final_error_message(interaction,
                                                f'You cannot use `{interaction.command.name}` '
                                                f'without the {error.missing_role} role.',
                                                error)

        elif isinstance(error, app_commands.CommandNotFound):
            LOGGER.info('User %s tried to use an invalid command.', interaction.user)
            await self.send_final_error_message(interaction,
                                                f'**{interaction.user.name}** this command does not exist.', error)

        elif isinstance(error, app_commands.CommandSignatureMismatch):
            LOGGER.info('User %s tried to use %s with invalid arguments. [%s]', interaction.user,
                        interaction.command.name,
                        error)
            await self.send_final_error_message(interaction,
                                                f'You cannot use `{interaction.command.name}` '
                                                f'with those arguments.\n```{error}```',
                                                error)

        elif isinstance(error, app_commands.CommandOnCooldown):
            LOGGER.info('User %s tried to use %s on cooldown. [%s]', interaction.user, interaction.command.name, error)
            await self.send_final_error_message(interaction,
                                                f'You cannot use `{interaction.command.name}` '
                                                f'on cooldown.\n```{error}```',
                                                error)

        elif isinstance(error, errors.UserNotConnectedToVoice):
            LOGGER.info('User %s tried to use %s without being connected to a voice channel.', interaction.user,
                        interaction.command.name)
            await self.send_error_message(interaction,
                                          f'You cannot use `{interaction.command.name}` '
                                          f'without being connected to a voice channel.',
                                          error)

        elif isinstance(error, errors.BotNotConnectedToVoice):
            LOGGER.info('User %s tried to use %s without the bot being connected to a voice channel.', interaction.user,
                        interaction.command.name)
            await self.send_error_message(interaction,
                                          f'You cannot use `{interaction.command.name}` '
                                          f'without the bot being connected to a voice channel.',
                                          error)

        elif isinstance(error, errors.BotNotPlayingAudio):
            LOGGER.info('User %s tried to use %s without the bot playing audio.', interaction.user,
                        interaction.command.name)
            await self.send_error_message(interaction,
                                          f'You cannot use `{interaction.command.name}` '
                                          f'without the bot playing audio.',
                                          error)

        else:
            LOGGER.error("Uncaught error caused by %s using %s. [%s]", interaction.user, interaction.data, error)
            await self.send_error_message(interaction, f'An error occurred while using `{interaction.command.name}`.',
                                          error)

    @staticmethod
    async def send_error_message(interaction: discord.Interaction, description: str,
                                 error: app_commands.AppCommandError):
        """ Send an error message. """
        embed = discord.Embed(
            title=error.__class__.__name__,
            description=f':no_entry_sign: **{interaction.user.mention}**'
        )

        embed.add_field(name="Description", value=f"{description}")

        if str(error) != "":
            embed.add_field(name="Error", value=f"```{error}```")

        await interaction.followup.send(embed=embed, ephemeral=True)

    @staticmethod
    async def send_final_error_message(interaction: discord.Interaction, description: str,
                                       error: app_commands.AppCommandError):
        """ Send a final error message. """
        embed = discord.Embed(
            title=error.__class__.__name__,
            description=f':no_entry_sign: **{interaction.user.mention}**'
        )

        embed.add_field(name="Description", value=f"{description}")

        if str(error) != "":
            embed.add_field(name="Error", value=f"```{error}```")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: pibot.PiBot) -> None:
    """ Load the cog. """
    await bot.add_cog(ExceptionHandler(bot))
