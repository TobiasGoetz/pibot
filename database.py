"""
Custom database class for the application.
"""
import logging

import discord
import pymongo

LOGGER: logging.Logger = logging.getLogger('db')
DEFAULT_PREFIX = "."


class Database:
    """
    Custom database class for the application.
    """

    def __init__(self, client: pymongo.MongoClient):
        self.client = client
        self.db = self.client["discord"]
        self.guilds = self.db["guilds"]

    async def initialize_guild(self, guild: discord.Guild):
        """
        Initialize a guild in the database.
        :param guild: The guild to initialize.
        """
        guild_data = {
            "_id": guild.id,
            "name": guild.name
            # Additional initialization data can go here
        }
        # Use upsert to avoid duplicating entries
        self.guilds.update_one({"_id": guild.id}, {"$set": guild_data}, upsert=True)
        LOGGER.info("Added or updated %s in the database.", guild.name)

    async def remove_guild(self, guild: discord.Guild):
        """
        Remove a guild from the database.
        :param guild: The guild to remove.
        """
        self.guilds.delete_one({"id": guild.id})
        LOGGER.info("Removed %s from the database.", guild.name)

    async def check_if_guild_exists_else_initialize(self, guild: discord.Guild):
        """
        Check if a guild exists in the database. If not, add it.
        :param guild: The guild to check.
        """
        result = self.guilds.find_one({"id": guild.id})
        if result is None:
            await self.initialize_guild(guild)
            return False
        return True

    async def get_setting(self, guild: discord.Guild, setting: str):
        """
        Get a setting for a guild.
        :param guild: The guild to get the setting for.
        :param setting: The key for the setting to get.
        :return: The value of the setting.
        """
        guild_data = self.guilds.find_one({"id": guild.id})
        if guild_data is not None and "settings" in guild_data and setting in guild_data["settings"]:
            return guild_data["settings"][setting]
        return None

    async def set_setting(self, guild: discord.Guild, setting: str, value):
        """
        Set a setting for a guild.
        :param guild: The guild to set the setting for.
        :param setting: The key for the setting to set.
        :param value: The value to set the setting to.
        """
        self.guilds.update_one({"id": guild.id}, {"$set": {f"settings.{setting}": value}})
        LOGGER.info("Updated %s to %s for %s.", setting, value, guild.name)

    async def get_prefix(self, message: discord.Message):
        """
        Get the prefix for a guild.
        :param _: The bot.
        :param message: The message including guild info to get the prefix for.
        :return: The prefix.
        """
        LOGGER.info("Getting prefix for %s.", message.guild)
        return await self.get_setting(message.guild, "prefix") or DEFAULT_PREFIX
