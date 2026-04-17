"""The custom bot class for PiBot."""

import asyncio
import logging
import os
import pathlib
from importlib.metadata import PackageNotFoundError, version

import discord.ext.commands
import pymongo

from pibot.database import Database
from pibot.settings import COMMAND_SYNC_BEHAVIOR, command_sync_behavior, is_dev_tools

logger = logging.getLogger("pibot")


def _log_level() -> int:
    """``LOG_LEVEL`` (default ``INFO``). Accepts standard ``logging`` level names."""
    raw = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    return getattr(logging, raw, logging.INFO)


def getVersion() -> str:
    """Return the bot version from package metadata (pyproject.toml)."""
    try:
        return version("pibot-discord")
    except PackageNotFoundError:
        return "dev"


class Bot(discord.ext.commands.Bot):
    """The custom bot class for PiBot."""

    @property
    def version(self) -> str:
        """Return the bot version from package metadata."""
        return getVersion()

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the bot."""
        self.database = Database(pymongo.MongoClient(os.getenv("MONGODB_URI")))
        self.commandSyncBehavior = command_sync_behavior()
        self.isDevTools = is_dev_tools()
        super().__init__(
            *args,
            # command_prefix=self.database.get_prefix,
            **kwargs,
        )

    async def setup_hook(self) -> None:
        """Set up the hooks for the bot."""
        discord.utils.setup_logging(level=_log_level())
        logger.info("Starting PiBot version %s", self.version)
        logger.info("Logged in as %s", self.user)
        await self.load_cogs()

    async def on_ready(self) -> None:
        """When the bot is ready."""
        logger.info("Ready as %s", self.user)
        await self.sync_commands()

    async def load_cogs(self) -> None:
        """Load all cogs."""
        package_dir = pathlib.Path(__file__).parent
        cogs = [p.stem for p in (package_dir / "cogs").glob("*.py") if p.stem != "__init__"]
        for cog in cogs:
            await self.load_extension(name=f".cogs.{cog}", package="pibot")
            logger.info("Loaded %s cog.", cog)
        else:
            logger.info("All cogs loaded.")

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """When the bot joins a guild."""
        logger.debug("Joined guild %s", guild.name)
        await self.database.initialize_guild(guild)

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """When the bot leaves a guild."""
        logger.debug("Left guild %s", guild.name)
        await self.database.remove_guild(guild)

    async def on_guild_available(self, guild: discord.Guild) -> None:
        """When a guild becomes available."""
        logger.debug("Guild %s is available", guild.name)
        await self.database.check_if_guild_exists_else_initialize(guild)

    async def on_message(self, message: discord.Message, /) -> None:
        """When a message is sent."""
        if message.guild is None:
            return

        if message.author.bot:
            return

        prefixes = await self.database.get_prefix(message)
        for pref in prefixes:
            if not message.content.lower().startswith(pref):
                continue

            default_command_channel = discord.utils.get(
                self.get_all_channels(),
                guild__name=message.guild.name,
                name="botspam",
            )
            command_channel = (
                message.guild.get_channel(await self.database.get_setting(message.guild, "command_channel"))
                or default_command_channel
            )

            if command_channel is not None and message.channel.id != command_channel.id:
                await message.delete()
                response = await message.channel.send(
                    embed=discord.Embed(
                        description=f":no_entry_sign: **{message.author.name}** "
                        f"you can only use commands in {command_channel.mention}."
                    )
                )
                await asyncio.sleep(5)
                await response.delete()

            return await self.process_commands(message)

    async def sync_commands(self) -> None:
        """Sync the app commands with Discord (see ``commandSyncBehavior``)."""
        logger.debug("Command sync behavior: %s.", self.commandSyncBehavior.value)
        if self.commandSyncBehavior is COMMAND_SYNC_BEHAVIOR.GLOBAL:
            logger.debug("Syncing application commands globally.")
            await self.tree.sync()
