"""Discord Bot."""

import asyncio
import os

import discord
from dotenv import load_dotenv

from pibot.bot import Bot


async def main():
    """Run the bot."""
    bot = Bot(command_prefix=".", case_insensitive=True, intents=discord.Intents.all())
    await bot.start(os.getenv("DISCORD_TOKEN"))


def run():
    """Entry point for the CLI."""
    load_dotenv()
    if not os.getenv("DISCORD_TOKEN"):
        raise ValueError("No Discord token found in environment variables")
    if not os.getenv("MONGODB_URI"):
        raise ValueError("No MongoDB URI found in environment variables")
    asyncio.run(main())

if __name__ == "__main__":
    run()
