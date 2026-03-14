"""Discord Bot."""

import asyncio
import os

import discord
from dotenv import load_dotenv

from pibot.bot import Bot


async def main(token: str) -> None:
    """Run the bot."""
    bot = Bot(command_prefix=".", case_insensitive=True, intents=discord.Intents.all())
    await bot.start(token)


def run() -> None:
    """Entry point for the CLI."""
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("No Discord token found in environment variables")
    if not os.getenv("MONGODB_URI"):
        raise ValueError("No MongoDB URI found in environment variables")
    asyncio.run(main(token))


if __name__ == "__main__":
    run()
