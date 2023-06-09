"""
Discord Bot
"""
import asyncio
import logging
import os

import discord
from discord import app_commands
from pymongo import MongoClient

import errors
import pibot

TOKEN = os.getenv('DISCORD_TOKEN')
OVERWRITE_PREFIX = os.getenv('DISCORD_PREFIX')
DB_CLIENT = MongoClient(os.getenv('MONGODB_URI'))
DB = DB_CLIENT['discord']
logger = logging.getLogger('discord')

# Bot
bot = pibot.PiBot(command_prefix=".", case_insensitive=True, intents=discord.Intents.all())


# Commands
@bot.tree.command(name="ping", description="Displays the bots ping")
async def ping(interaction):
    """ Displays the bots ping. """
    await interaction.response.send_message(f"Ping: {bot.latency * 1000:.0f}ms", ephemeral=True)


# Error handling
@bot.tree.error
async def on_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    """ When a command has an error. """
    if isinstance(error, app_commands.MissingPermissions):
        logger.info('User %s tried to use %s without permissions.', interaction.user, interaction.command.name)
        await send_final_error_message(interaction, f'You cannot use `{interaction.command.name}`.', error)

    elif isinstance(error, app_commands.MissingRole):
        logger.info(
            'User %s tried to use %s without the %s role.',
            interaction.user, interaction.command.name, error.missing_role
        )
        await send_final_error_message(interaction,
                                       f'You cannot use `{interaction.command.name}` '
                                       f'without the {error.missing_role} role.',
                                       error)

    elif isinstance(error, app_commands.CommandNotFound):
        logger.info('User %s tried to use an invalid command.', interaction.user)
        await send_final_error_message(interaction,
                                       f'**{interaction.user.name}** this command does not exist.', error)

    elif isinstance(error, app_commands.CommandSignatureMismatch):
        logger.info('User %s tried to use %s with invalid arguments. [%s]', interaction.user, interaction.command.name,
                    error)
        await send_final_error_message(interaction,
                                       f'You cannot use `{interaction.command.name}` '
                                       f'with those arguments.\n```{error}```',
                                       error)

    elif isinstance(error, app_commands.CommandOnCooldown):
        logger.info('User %s tried to use %s on cooldown. [%s]', interaction.user, interaction.command.name, error)
        await send_final_error_message(interaction,
                                       f'You cannot use `{interaction.command.name}` on cooldown.\n```{error}```',
                                       error)

    elif isinstance(error, errors.UserNotConnectedToVoice):
        logger.info('User %s tried to use %s without being connected to a voice channel.', interaction.user,
                    interaction.command.name)
        await send_error_message(interaction,
                                 f'You cannot use `{interaction.command.name}` '
                                 f'without being connected to a voice channel.',
                                 error)

    elif isinstance(error, errors.BotNotConnectedToVoice):
        logger.info('User %s tried to use %s without the bot being connected to a voice channel.', interaction.user,
                    interaction.command.name)
        await send_error_message(interaction,
                                 f'You cannot use `{interaction.command.name}` '
                                 f'without the bot being connected to a voice channel.',
                                 error)

    elif isinstance(error, errors.BotNotPlayingAudio):
        logger.info('User %s tried to use %s without the bot playing audio.', interaction.user,
                    interaction.command.name)
        await send_error_message(interaction,
                                 f'You cannot use `{interaction.command.name}` '
                                 f'without the bot playing audio.',
                                 error)

    else:
        logger.error("Uncaught error caused by %s using %s. [%s]", interaction.user, interaction.data, error)
        await send_error_message(interaction, f'An error occurred while using `{interaction.command.name}`.', error)


async def send_error_message(interaction: discord.Interaction, description: str, error: app_commands.AppCommandError):
    """ Send an error message. """
    embed = discord.Embed(
        title=error.__class__.__name__,
        description=f':no_entry_sign: **{interaction.user.mention}**'
    )

    embed.add_field(name="Description", value=f"{description}")

    if str(error) != "":
        embed.add_field(name="Error", value=f"```{error}```")

    await interaction.followup.send(embed=embed, ephemeral=True)


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


# Run
async def main():
    """ Run the bot. """
    async with bot:
        await bot.start(TOKEN)


if __name__ == '__main__':
    asyncio.run(main())
