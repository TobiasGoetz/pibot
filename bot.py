"""
Discord Bot
"""
import asyncio
import logging
import os
from pathlib import Path

import discord
from discord.ext import commands
from pymongo import MongoClient

TOKEN = os.getenv('DISCORD_TOKEN')
OVERWRITE_PREFIX = os.getenv('DISCORD_PREFIX')
DB_CLIENT = MongoClient(os.getenv('MONGODB_URI'))
DB = DB_CLIENT['discord']
logger = logging.getLogger('discord')

DEFAULT_PREFIX = "."


# Database interaction
async def db_initialize_guild(guild):
    """
    Initialize a guild in the database.
    :param guild: The guild to initialize.
    """
    DB.guilds.insert_one({"id": guild.id, "name": guild.name})
    logger.info("Added %s to the database.", guild.name)


async def db_remove_guild(guild):
    """
    Remove a guild from the database.
    :param guild: The guild to remove.
    """
    DB.guilds.delete_one({"id": guild.id})
    logger.info("Removed %s from the database.", guild.name)


async def db_check_if_guild_exists_else_initialize(guild):
    """
    Check if a guild exists in the database. If not, add it.
    :param guild: The guild to check.
    """
    result = DB.guilds.find_one({"id": guild.id})
    if result is None:
        await db_initialize_guild(guild)
        return False
    return True


async def get_prefix(_, message):
    """
    Get the prefix for a guild.
    :param _: The bot.
    :param message: The message including guild info to get the prefix for.
    :return: The prefix.
    """
    return OVERWRITE_PREFIX or await get_setting(message.guild, "prefix") or DEFAULT_PREFIX


async def get_setting(guild: discord.Guild, setting):
    """
    Get a setting for a guild.
    :param guild: The guild to get the setting for.
    :param setting: The key for the setting to get.
    :return: The value of the setting.
    """
    guild_data = DB.guilds.find_one({"id": guild.id})
    if guild_data is not None and "settings" in guild_data and setting in guild_data["settings"]:
        return guild_data["settings"][setting]
    return None


async def set_setting(guild: discord.Guild, setting, value):
    """
    Set a setting for a guild.
    :param guild: The guild to set the setting for.
    :param setting: The key for the setting to set.
    :param value: The value to set the setting to.
    """
    DB.guilds.update_one({"id": guild.id}, {"$set": {f"settings.{setting}": value}})
    logger.info("Updated %s to %s for %s.", setting, value, guild.name)


# Bot
bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, intents=discord.Intents.all())


# Events
@bot.event
async def on_ready():
    """ When the bot is ready. """
    logger.info('Logged in as %s', bot.user)
    await load_cogs()
    await bot.tree.sync()


@bot.event
async def on_guild_join(guild):
    """ When the bot joins a guild. """
    await db_initialize_guild(guild)


@bot.event
async def on_guild_remove(guild):
    """ When the bot leaves a guild. """
    await db_remove_guild(guild)


@bot.event
async def on_guild_available(guild):
    """ When the bot is available in a guild. """
    await db_check_if_guild_exists_else_initialize(guild)


@bot.event
async def on_message(message):
    """ When a message is sent. """
    prefixes = await get_prefix(bot, message)
    for pref in prefixes:
        if message.content.lower().startswith(pref):
            default_command_channel = discord.utils.get(bot.get_all_channels(), guild__name=message.guild.name,
                                                        name='botspam')
            command_channel = message.guild.get_channel(
                await get_setting(message.guild, "command_channel")) or default_command_channel

            if message.channel.id == command_channel.id:
                return await bot.process_commands(message)

            await message.delete()
            response = await message.channel.send(
                embed=discord.Embed(
                    description=
                    f':no_entry_sign: **{message.author.name}** you can only use commands in {command_channel.mention}.'
                ))
            await asyncio.sleep(5)
            await response.delete()


# Commands
@bot.tree.command(name="ping", description="Displays the bots ping")
async def ping(interaction):
    """ Displays the bots ping. """
    await interaction.response.send_message(f"Ping: {bot.latency * 1000:.0f}ms", ephemeral=True)


# Error handling
@bot.event
async def on_command_error(ctx, error):
    """ When a command has an error. """
    if isinstance(error, commands.MissingPermissions):
        logger.info('User %s tried to use %s without permissions.', ctx.author, ctx.command)
        await send_error_message(ctx, f'You cannot use `{ctx.command}`.', error)

    if isinstance(error, commands.MissingRole):
        logger.info(
            'User %s tried to use %s without the %s role.',
            ctx.author, ctx.command, error.missing_role
        )
        await send_error_message(ctx, f'You cannot use `{ctx.command}` without the {error.missing_role} role.', error)

    if isinstance(error, commands.CommandNotFound):
        logger.info('User %s tried to use an invalid command.', ctx.author)
        await send_error_message(ctx, f':no_entry_sign: **{ctx.author.name}** this command does not exist.', error)

    if isinstance(error, commands.BadArgument):
        logger.info('User %s tried to use %s with invalid arguments. [%s]', ctx.author, ctx.command, error)
        await send_error_message(ctx, f'You cannot use `{ctx.command}` with those arguments.\n```{error}```', error)

    if isinstance(error, commands.CommandOnCooldown):
        logger.info('User %s tried to use %s on cooldown. [%s]', ctx.author, ctx.command, error)
        await send_error_message(ctx, f'You cannot use `{ctx.command}` on cooldown.\n```{error}```', error)


async def send_error_message(ctx, description, error):
    """ Send an error message. """
    await ctx.send(
        embed=discord.Embed(
            title={error},
            description=
            f':no_entry_sign: **{ctx.author.name}** {description}\n'
            f'```{error}```',
        )
    )


# Loading Cogs
async def load_cogs():
    """ Load all cogs. """
    cogs = [p.stem for p in Path("./cogs").glob("*.py")]
    for cog in cogs:
        await bot.load_extension(f"cogs.{cog}")
        logger.info("Loaded %s cog.", cog)


# Run
async def main():
    """ Run the bot. """
    discord.utils.setup_logging()
    async with bot:
        await bot.start(TOKEN)


if __name__ == '__main__':
    asyncio.run(main())
