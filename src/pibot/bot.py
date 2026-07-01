"""The custom bot class for PiBot."""

import asyncio
import logging
import pathlib
from importlib.metadata import PackageNotFoundError, version

import discord
import discord.ext.commands
from pymongo import AsyncMongoClient

from pibot.config import COMMAND_SYNC_BEHAVIOR, BotConfig
from pibot.cogs.general.config import GeneralConfig
from pibot.guild_settings.service import GuildSettingsService
from pibot.guild_settings.store import SettingsStore

logger = logging.getLogger("pibot")


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

    def __init__(self, config: BotConfig, *args, **kwargs) -> None:
        """Initialize the bot."""
        self.config = config
        mongoClient = AsyncMongoClient(config.mongodbUri)
        self.guildSettings = GuildSettingsService(SettingsStore(mongoClient))
        self.commandSyncBehavior = config.commandSyncBehavior
        self.isDevTools = config.enableDevTools
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        """Set up the hooks for the bot."""
        discord.utils.setup_logging(level=self.config.logLevelValue)
        logger.info("Starting PiBot version %s", self.version)
        logger.info("Logged in as %s", self.user)
        await self.load_cogs()

    async def on_ready(self) -> None:
        """When the bot is ready."""
        logger.info("Ready as %s", self.user)
        await self.sync_commands()

    async def load_cogs(self) -> None:
        """Load all cogs (flat modules and feature packages)."""
        cogs_dir = pathlib.Path(__file__).parent / "cogs"
        extensions: list[str] = []
        for path in sorted(cogs_dir.glob("*.py")):
            if path.stem != "__init__":
                extensions.append(f".cogs.{path.stem}")
        for path in sorted(cogs_dir.iterdir()):
            if path.is_dir() and (path / "__init__.py").exists():
                extensions.append(f".cogs.{path.name}")
        for extension in extensions:
            await self.load_extension(name=extension, package="pibot")
            logger.info("Loaded %s.", extension.rsplit(".", 1)[-1])
        else:
            logger.info("All cogs loaded.")

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """When the bot joins a guild."""
        logger.debug("Joined guild %s", guild.name)

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """When the bot leaves a guild."""
        logger.debug("Left guild %s", guild.name)

    async def on_guild_available(self, guild: discord.Guild) -> None:
        """When a guild becomes available."""
        logger.debug("Guild %s is available", guild.name)

    async def on_message(self, message: discord.Message, /) -> None:
        """When a message is sent."""
        if message.guild is None:
            return

        if message.author.bot:
            return

        general = await self.guildSettings.getFeature(message.guild.id, GeneralConfig)
        if not message.content.lower().startswith(general.prefix.lower()):
            return

        default_command_channel = discord.utils.get(
            self.get_all_channels(),
            guild__name=message.guild.name,
            name="botspam",
        )
        commandChannelId = general.commandChannelId
        command_channel = message.guild.get_channel(commandChannelId) if commandChannelId else default_command_channel

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
