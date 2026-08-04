"""Discord Bot."""

import asyncio

import discord
from dotenv import load_dotenv

from pibot.bot import Bot
from pibot.config import BotConfig


async def main(config: BotConfig) -> None:
    """Run the bot."""
    bot = Bot(config, command_prefix=".", case_insensitive=True, intents=discord.Intents.all())
    await bot.start(config.discordToken)


def run() -> None:
    """Entry point for the CLI."""
    load_dotenv()
    config = BotConfig()
    asyncio.run(main(config))


if __name__ == "__main__":
    run()
