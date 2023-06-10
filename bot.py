"""
Discord Bot
"""
import asyncio
import logging
import os

import discord
from pymongo import MongoClient

import pibot

TOKEN = os.getenv('DISCORD_TOKEN')
OVERWRITE_PREFIX = os.getenv('DISCORD_PREFIX')
DB_CLIENT = MongoClient(os.getenv('MONGODB_URI'))
DB = DB_CLIENT['discord']
logger = logging.getLogger('discord')


async def main():
    """ Run the bot. """
    bot = pibot.PiBot(command_prefix=".", case_insensitive=True, intents=discord.Intents.all())
    await bot.start(TOKEN)


if __name__ == '__main__':
    asyncio.run(main())
