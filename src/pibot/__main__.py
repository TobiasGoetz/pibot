"""Discord Bot."""

import asyncio
import os

import discord

from pibot.pibot import PiBot

TOKEN = os.getenv("DISCORD_TOKEN")


async def main():
    """Run the bot."""
    bot = PiBot(command_prefix=".", case_insensitive=True, intents=discord.Intents.all())
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
