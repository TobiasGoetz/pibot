# bot.py
import asyncio
import os
from pathlib import Path

import discord
import wavelink
from discord.ext import commands

TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='.', case_insensitive=True, intents=discord.Intents.all())


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    await load_cogs()


@bot.event
async def on_message(message):
    cmdchannel = discord.utils.get(bot.get_all_channels(), guild__name=message.guild.name, name='botspam')
    if message.content.lower().startswith(getattr(bot, 'command_prefix')):
        if message.channel.id == cmdchannel.id:
            await bot.process_commands(message)
        else:
            await message.channel.send(f'Write this command in {cmdchannel.mention}')


@bot.command(help="Displays the bots ping")
async def ping(ctx):
    await ctx.send(f"Ping: {bot.latency * 1000:.0f}ms")


async def load_cogs():
    cogs = [p.stem for p in Path("./cogs").glob("*.py")]
    for cog in cogs:
        await bot.load_extension(f"cogs.{cog}")
        print(f"Loaded '{cog}' cog.")


async def main():
    async with bot:
        await bot.start(TOKEN)


if __name__ == '__main__':
    asyncio.run(main())
