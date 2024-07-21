"""
Admin cog
"""
import logging

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("discord.admin")


class Admin(commands.Cog):
    """
    Admin commands
    """

    group = app_commands.Group(name="admin", description="Admin commands for the bot.")

    def __init__(self, bot):
        self.bot = bot

    @group.command(name="prefix", description="Set the prefix for the guild.")
    @app_commands.checks.has_permissions(administrator=True)
    async def prefix(self, interaction: discord.Interaction, arg: str):
        """
        Set the prefix for the guild.
        :param interaction: The interaction of the slash command.
        :param arg: The prefix to set.
        """
        await interaction.response.defer()

        await self.bot.database.check_if_guild_exists_else_initialize(interaction.guild)
        await self.bot.database.set_setting(interaction.guild, "prefix", arg)

        logger.info("Changed prefix for %s to %s.", interaction.guild.name, arg)
        await interaction.followup.send(f"Prefix set to {arg}")

    @group.command(name="command_channel", description="Set the command channel for the guild.")
    @app_commands.checks.has_permissions(administrator=True)
    async def command_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """
        Set the command channel for the guild.
        :param channel: The channel to set as the command channel.
        :param interaction: The interaction of the slash command.
        """
        await interaction.response.defer()

        await self.bot.database.check_if_guild_exists_else_initialize(interaction.guild)

        if channel is None:
            return await interaction.followup.send(f"Channel {channel} not found.")

        await self.bot.database.set_setting(interaction.guild, "command_channel", channel.id)
        logger.info(
            "Changed command channel for %s to %s.",
            interaction.guild.name,
            channel.name,
        )
        await interaction.followup.send(f"Command channel set to {channel.mention}")

    @group.command(name="clear", description="Clear a specified amount of messages.")
    @app_commands.checks.has_permissions(administrator=True)
    async def clear(self, interaction: discord.Interaction, amount: int = 1) -> None:
        """
        Clear a specified amount of messages.
        :param interaction: The interaction of the slash command.
        :param amount: The amount of messages to clear.
        """
        await interaction.response.defer()
        await interaction.channel.purge(limit=amount + 1)
        logging.info(
            "User %s cleared %s messages in %s.",
            interaction.user,
            amount,
            interaction.channel,
        )

    @group.command(name="mute", description="Mute a member.")
    @app_commands.checks.has_permissions(administrator=True)
    async def mute(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            *,
            reason: str = None,
    ) -> None:
        """
        Mute a member.
        :param interaction: The interaction of the slash command.
        :param member: The member to mute.
        :param reason: The reason for the mute.
        """
        await interaction.response.defer()
        role = discord.utils.get(interaction.guild.roles, name="Muted")

        if role is None:
            logger.info("Muted role not found, creating one.")
            await interaction.guild.create_role(name="Muted")
            role = discord.utils.get(interaction.guild.roles, name="Muted")

        for channel in interaction.guild.channels:
            await channel.set_permissions(role, speak=False, send_messages=False)
        logger.info("Muted role created.")

        await member.add_roles(role)

        if reason is None:
            await interaction.followup.send(f"{member.mention} has been muted.")
        else:
            await interaction.followup.send(f"{member.mention} has been muted for {reason}")
        logging.info("User %s muted %s for %s.", interaction.user, member, reason)

    @group.command(name="unmute", description="Unmute a member.")
    @app_commands.checks.has_permissions(administrator=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        """
        Unmute a member.
        :param interaction: The interaction of the slash command.
        :param member: The member to unmute.
        """
        await interaction.response.defer()
        role = discord.utils.get(interaction.guild.roles, name="Muted")
        await member.remove_roles(role)
        await interaction.followup.send(f"{member.mention} has been unmuted.")
        logging.info("User %s unmuted %s.", interaction.user, member)


async def setup(bot):
    """Setup the cog."""
    await bot.add_cog(Admin(bot))
