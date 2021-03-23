# bot.py
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='.')


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


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


bot.run(TOKEN)
