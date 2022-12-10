"""
Discord Bot
"""
import asyncio
import logging
import os
from pathlib import Path

import discord
import psycopg2
from discord.ext import commands

TOKEN = os.getenv('DISCORD_TOKEN')
OVERWRITE_PREFIX = os.getenv('DISCORD_PREFIX')
DB = psycopg2.connect(os.getenv('DATABASE_URL'), sslmode='require')
logger = logging.getLogger('discord')

DEFAULT_PREFIX = "."


# Database interaction
async def db_initialize_guild(guild):
    """
    Initialize a guild in the database.
    :param guild: The guild to initialize.
    """
    with DB.cursor() as cursor:
        cursor.execute("INSERT INTO discord.guilds (id, name) VALUES (%s, %s)", (guild.id, guild.name))
        DB.commit()
        logger.info("Added %s to the database.", guild.name)


async def db_remove_guild(guild):
    """
    Remove a guild from the database.
    :param guild: The guild to remove.
    """
    with DB.cursor() as cursor:
        cursor.execute("DELETE FROM discord.guilds WHERE id = %s", (guild.id,))
        DB.commit()
        logger.info("Removed %s from the database.", guild.name)


async def db_check_if_guild_exists_else_initialize(guild):
    """
    Check if a guild exists in the database. If not, add it.
    :param guild: The guild to check.
    """
    with DB.cursor() as cursor:
        cursor.execute("SELECT id FROM discord.guilds WHERE id = %s", (guild.id,))
        result = cursor.fetchone()
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
    with DB.cursor() as cursor:
        cursor.execute("SELECT value FROM discord.settings WHERE guild_id = %s AND key = %s", (guild.id, setting))
        result = cursor.fetchone()
        if result is None:
            return None
        return result[0]


async def set_setting(guild: discord.Guild, setting, value):
    """
    Set a setting for a guild.
    :param guild: The guild to set the setting for.
    :param setting: The key for the setting to set.
    :param value: The value to set the setting to.
    """
    if await get_setting(guild, setting) is not None:
        with DB.cursor() as cursor:
            cursor.execute(
                "UPDATE discord.settings SET value = %s WHERE guild_id = %s AND key = %s", (value, guild.id, setting)
            )
            DB.commit()
        logger.info("Updated %s to %s for %s.", setting, value, guild.name)
    else:
        with DB.cursor() as cursor:
            cursor.execute(
                "INSERT INTO discord.settings (guild_id, key, value) VALUES (%s, %s, %s)", (guild.id, setting, value)
            )
            DB.commit()
        logger.info("Added %s with value %s for %s.", setting, value, guild.name)


# Bot
bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, intents=discord.Intents.all())


# Events
@bot.event
async def on_ready():
    """ When the bot is ready. """
    logger.info('Logged in as %s', bot.user)
    await load_cogs()


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
    cmdchannel = discord.utils.get(bot.get_all_channels(), guild__name=message.guild.name, name='botspam')
    prefixes = await get_prefix(bot, message)
    for pref in prefixes:
        if message.content.lower().startswith(pref):
            if message.channel.id == cmdchannel.id:
                return await bot.process_commands(message)
            return await message.channel.send(f'Write this command in {cmdchannel.mention}')


# Commands
@bot.command(help="Displays the bots ping")
async def ping(ctx):
    """ Displays the bots ping. """
    await ctx.send(f"Ping: {bot.latency * 1000:.0f}ms")


@bot.command()
async def prefix(ctx, arg):
    """
    Set the prefix for the guild.
    :param ctx: The context of the command.
    :param arg: The prefix to set.
    """
    await db_check_if_guild_exists_else_initialize(ctx.guild)
    await set_setting(ctx.guild, "prefix", arg)
    logger.info("Changed prefix for %s to %s.", ctx.guild.name, arg)
    await ctx.send(f"Prefix set to {arg}")


# Error handling
@bot.event
async def on_command_error(ctx, error):
    """ When a command has an error. """
    if isinstance(error, commands.MissingPermissions):
        logger.info('User %s tried to use %s without permissions.', ctx.author, ctx.command)
        await ctx.send(
            embed=discord.Embed(
                description=f':no_entry_sign: **{ctx.author.name}** you cannot use `{ctx.command}`.',
            )
        )

    if isinstance(error, commands.MissingRole):
        logger.info(
            'User %s tried to use %s without the %s role.',
            ctx.author, ctx.command, error.missing_role
        )
        await ctx.send(
            embed=discord.Embed(
                description=
                f':no_entry_sign: **{ctx.author.name}** you cannot use `{ctx.command}`'
                f'without the {error.missing_role} role.',
            )
        )

    if isinstance(error, commands.CommandNotFound):
        logger.info('User %s tried to use an invalid command.', ctx.author)
        await ctx.send(
            embed=discord.Embed(
                description=f':no_entry_sign: **{ctx.author.name}** this command does not exist.',
            )
        )

    if isinstance(error, commands.BadArgument):
        logger.info('User %s tried to use %s with invalid arguments. [%s]', ctx.author, ctx.command, error)
        await ctx.send(
            embed=discord.Embed(
                description=
                f':no_entry_sign: **{ctx.author.name}** you cannot use `{ctx.command}` with those arguments.\n'
                f'```{error}```',
            )
        )

    if isinstance(error, commands.CommandOnCooldown):
        logger.info('User %s tried to use %s on cooldown. [%s]', ctx.author, ctx.command, error)
        await ctx.send(
            embed=discord.Embed(
                description=
                f':no_entry_sign: **{ctx.author.name}** you cannot use `{ctx.command}` on cooldown.\n'
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
