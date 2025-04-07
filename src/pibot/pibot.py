"""The custom bot class for PiBot."""

import asyncio
import importlib
import logging
import os
import pathlib

import discord.ext.commands
import pymongo

from pibot.database import Database

logger = logging.getLogger("pibot")

class PiBot(discord.ext.commands.Bot):
    """The custom bot class for PiBot."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the bot."""
        self.database = Database(pymongo.MongoClient(os.getenv("MONGODB_URI")))
        super().__init__(
            *args,
            # command_prefix=self.database.get_prefix,
            **kwargs,
        )

    async def setup_hook(self) -> None:
        """Set up the hooks for the bot."""
        discord.utils.setup_logging()
        logger.info("Logged in as %s", self.user)
        await self.load_cogs()
        await self.tree.sync()

    async def on_ready(self) -> None:
        """When the bot is ready."""
        logger.info("Ready as %s", self.user)

    async def load_cogs(self) -> None:
        """Load all cogs."""
        package_dir = pathlib.Path(importlib.resources.files("pibot"))
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

        prefixes = await self.database.get_prefix(message)
        for pref in prefixes:
            if message.content.lower().startswith(pref):
                default_command_channel = discord.utils.get(
                    self.get_all_channels(),
                    guild__name=message.guild.name,
                    name="botspam",
                )
                command_channel = (
                    message.guild.get_channel(await self.database.get_setting(message.guild, "command_channel"))
                    or default_command_channel
                )

                if message.channel.id == command_channel.id:
                    return await self.process_commands(message)

                await message.delete()
                response = await message.channel.send(
                    embed=discord.Embed(
                        description=f":no_entry_sign: **{message.author.name}** "
                        f"you can only use commands in {command_channel.mention}."
                    )
                )
                await asyncio.sleep(5)
                await response.delete()
