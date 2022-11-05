# bot.py
import asyncio
import logging
import os
from pathlib import Path

import discord
import psycopg2
from discord.ext import commands

TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('DISCORD_PREFIX')
db = psycopg2.connect(os.getenv('DATABASE_URL'), sslmode='require')
logger = logging.getLogger('discord')


async def get_prefix(bot, message):
    if PREFIX:
        return PREFIX

    await db_check_if_guild_exists(message.guild)
    with db.cursor() as cursor:
        cursor.execute("SELECT prefix FROM discord.settings WHERE guild_id = %s", (message.guild.id,))
        prefix = cursor.fetchone()
    return prefix


async def db_initialize_guild(guild):
    with db.cursor() as cursor:
        cursor.execute("INSERT INTO discord.settings (guild_id, prefix) VALUES (%s, %s)", (guild.id, "."))
        db.commit()
        logger.info(f"Added {guild.name} to the database.")


async def db_check_if_guild_exists(guild):
    with db.cursor() as cursor:
        cursor.execute("SELECT guild_id FROM discord.settings WHERE guild_id = %s", (guild.id,))
        result = cursor.fetchone()
    if result is None:
        await db_initialize_guild(guild)
        return False
    return True


bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, intents=discord.Intents.all())


@bot.event
async def on_ready():
    logger.info('Logged in as %s', bot.user)
    await load_cogs()


@bot.event
async def on_message(message):
    cmdchannel = discord.utils.get(bot.get_all_channels(), guild__name=message.guild.name, name='botspam')
    prefixes = await get_prefix(bot, message)
    for prefix in prefixes:
        if message.content.lower().startswith(prefix):
            if message.channel.id == cmdchannel.id:
                return await bot.process_commands(message)
            else:
                return await message.channel.send(f'Write this command in {cmdchannel.mention}')


@bot.command(help="Displays the bots ping")
async def ping(ctx):
    await ctx.send(f"Ping: {bot.latency * 1000:.0f}ms")


@bot.command()
async def prefix(ctx, arg):
    await db_check_if_guild_exists(ctx.guild)
    with db.cursor() as cursor:
        cursor.execute("UPDATE discord.settings SET prefix = %s WHERE guild_id = %s", (arg, ctx.guild.id))
        db.commit()
    logger.info(f"Changed prefix for {ctx.guild.name} to {arg}")
    await ctx.send(f"Prefix set to {arg}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        logger.info(f'User {ctx.author} tried to use {ctx.command} without permissions.')
        await ctx.send(
            embed=discord.Embed(
                description=f':no_entry_sign: **{ctx.author.name}** you cannot use `{ctx.command}`.',
            )
        )

    if isinstance(error, commands.MissingRole):
        logger.info(f'User {ctx.author} tried to use {ctx.command} without the {error.missing_role} role.')
        await ctx.send(
            embed=discord.Embed(
                description=f':no_entry_sign: **{ctx.author.name}** you cannot use `{ctx.command}` without the {error.missing_role} role.',
            )
        )

    if isinstance(error, commands.CommandNotFound):
        logger.info(f'User {ctx.author} tried to use an invalid command.')
        await ctx.send(
            embed=discord.Embed(
                description=f':no_entry_sign: **{ctx.author.name}** this command does not exist.',
            )
        )


async def load_cogs():
    cogs = [p.stem for p in Path("./cogs").glob("*.py")]
    for cog in cogs:
        await bot.load_extension(f"cogs.{cog}")
        logger.info(f"Loaded {cog} cog.")


async def main():
    discord.utils.setup_logging()
    async with bot:
        await bot.start(TOKEN)


if __name__ == '__main__':
    asyncio.run(main())
